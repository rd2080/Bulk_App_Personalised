"""Log what was actually eaten. Plans are never changed or counted as eaten."""

from __future__ import annotations

from datetime import date

import streamlit as st

from bulking_app.repositories.food_inventory import list_foods
from bulking_app.repositories.recipe_library import list_recipes
from bulking_app.services import meal_logging as svc

st.set_page_config(page_title="Log what I ate | Bulk App", page_icon="🍴", layout="centered")
st.title("Log what I ate")
log_date = st.date_input("Day", value=date.today(), key="log_day")

try:
    summary = svc.day_summary(log_date)
    foods, recipes = list_foods(), list_recipes()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()


def _run(action):
    try:
        action()
        return True
    except (RuntimeError, ValueError) as exc:
        st.error(str(exc))
        return False


def _text(value):
    return "" if value is None else f"{value:g}"


with st.expander("Add what I ate", expanded=not summary["logs"]):
    kind = st.radio("Add from", ["Recipe", "Food", "Something else"], horizontal=True)
    with st.form("add_log", clear_on_submit=True):
        entry_fn = None
        if kind == "Recipe":
            pick = st.selectbox("Recipe", recipes, format_func=lambda r: r["recipe_name"]) if recipes else None
            qty = st.number_input("Amount eaten (g)", min_value=0.0, step=10.0, format="%g")
            st.caption("Nutrition is scaled from the recipe's total weight.")
            if pick:
                entry_fn = lambda: svc.recipe_entry(pick, qty)  # noqa: E731
            else:
                st.info("No recipes saved yet.")
        elif kind == "Food":
            pick = st.selectbox("Food", foods, format_func=lambda f: f["food_name"]) if foods else None
            qty = st.number_input("Amount", min_value=0.0, step=0.5, format="%g")
            unit = st.text_input("Unit", value=(pick or {}).get("unit") or "", placeholder="g, piece, cup")
            if pick:
                entry_fn = lambda: svc.food_entry(pick, qty, unit, extra_kcal, extra_protein)  # noqa: E731
            else:
                st.info("No foods saved yet.")
        else:
            name = st.text_input("What did you eat?", max_chars=160)
            qty = st.number_input("Amount", min_value=0.0, step=0.5, format="%g")
            unit = st.text_input("Unit", placeholder="g, piece, cup")
            entry_fn = lambda: svc.free_text_entry(name, qty, unit, extra_kcal, extra_protein)  # noqa: E731
        extra_kcal = extra_protein = None
        if kind != "Recipe":
            st.caption("Nutrition stays unknown unless you enter it.")
            extra_kcal = st.text_input("Calories (optional)", placeholder="leave blank if unknown")
            extra_protein = st.text_input("Protein g (optional)", placeholder="leave blank if unknown")
        if st.form_submit_button("Add", type="primary", use_container_width=True) and entry_fn:
            def _add():
                saved = svc.add_entry(log_date, entry_fn())
                st.session_state["flash"] = f"Saved: {saved['item_name']} ({svc.format_quantity(saved)})."
            if _run(_add):
                st.rerun()

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.subheader(f"Eaten on {log_date.isoformat()}")
st.caption(
    f"Known so far: {svc.format_value(summary['known_kcal'], 'kcal')}, "
    f"{svc.format_value(summary['known_protein_g'], 'g protein')}"
    + (" (incomplete: some items have unknown nutrition)" if summary["incomplete"] else "")
)
if not summary["logs"]:
    st.info("Nothing logged for this day yet.")

for log in summary["logs"]:
    with st.container(border=True):
        st.markdown(f"**{log['item_name']}** - {svc.format_quantity(log)}")
        st.caption(f"{svc.format_value(log['calories_kcal'], 'kcal')} | "
                   f"{svc.format_value(log['protein_g'], 'g protein')} | {log['nutrition_source']}")
        if st.button("Edit", key=f"edit_{log['id']}", use_container_width=True):
            st.session_state["editing_log"] = log["id"]
            st.rerun()
        if st.session_state.get("editing_log") == log["id"]:
            with st.form(f"edit_form_{log['id']}"):
                name = st.text_input("Name", value=log["item_name"], max_chars=160)
                qty = st.number_input("Amount", min_value=0.0, value=float(log["quantity"]), step=0.5, format="%g")
                unit = st.text_input("Unit", value=log["unit"])
                kcal = st.text_input("Calories", value=_text(log["calories_kcal"]))
                prot = st.text_input("Protein g", value=_text(log["protein_g"]))
                save, cancel, remove = st.columns(3)
                if save.form_submit_button("Save", type="primary"):
                    def _save():
                        entry = svc.edited_entry(log, name, qty, unit, kcal, prot)
                        svc.edit_entry(log["id"], log_date, entry, log["log_time"])
                        st.session_state.pop("editing_log", None)
                        st.session_state["flash"] = "Changes saved."
                    if _run(_save):
                        st.rerun()
                if cancel.form_submit_button("Cancel"):
                    st.session_state.pop("editing_log", None)
                    st.rerun()
                if remove.form_submit_button("Remove"):
                    st.session_state["confirm_remove"] = log["id"]
                    st.rerun()
        if st.session_state.get("confirm_remove") == log["id"]:
            st.warning("Remove this entry? It will no longer count toward today.")
            yes, no = st.columns(2)
            if yes.button("Yes, remove", key=f"yes_{log['id']}", type="primary"):
                def _remove():
                    svc.remove_entry(log["id"])
                    st.session_state.pop("confirm_remove", None)
                    st.session_state.pop("editing_log", None)
                    st.session_state["flash"] = "Entry removed."
                if _run(_remove):
                    st.rerun()
            if no.button("Keep it", key=f"no_{log['id']}"):
                st.session_state.pop("confirm_remove", None)
                st.rerun()
