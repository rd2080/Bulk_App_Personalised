"""Food inventory page."""

from __future__ import annotations

import streamlit as st

from bulking_app.repositories.food_inventory import (
    ALLOWED_AVAILABILITY_TYPES,
    add_food,
    list_foods,
    set_food_availability,
    update_food,
)

st.set_page_config(page_title="Food Inventory | Bulk App", page_icon="🥗", layout="wide")
st.title("Food Inventory")
st.caption("Maintain the foods currently available to the meal planner.")

LABELS = {
    "always_available": "Always available",
    "stock_tracked": "Stock tracked",
    "on_demand": "On demand",
}

with st.expander("Add food", expanded=False):
    with st.form("add_food_form", clear_on_submit=True):
        name = st.text_input("Food name", placeholder="Eggs")
        availability = st.selectbox(
            "Availability",
            ALLOWED_AVAILABILITY_TYPES,
            format_func=lambda value: LABELS[value],
        )
        quantity = st.number_input("Quantity (optional)", min_value=0.0, value=0.0, step=0.1)
        unit = st.text_input("Unit (optional)", placeholder="pieces, kg, L, servings")
        if st.form_submit_button("Add food", type="primary"):
            try:
                add_food(
                    food_name=name,
                    availability_type=availability,
                    quantity=None if quantity == 0 else quantity,
                    unit=unit,
                )
                st.success(f"Added {name.strip()} to your inventory.")
                st.rerun()
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

st.subheader("Inventory")
try:
    foods = list_foods()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()


def render_food(item: dict) -> None:
    quantity = ""
    if item["quantity"] is not None:
        quantity = f" · {item['quantity']:g} {item['unit'] or ''}".rstrip()

    with st.container(border=True):
        left, action = st.columns([5, 1])
        left.markdown(f"**{item['food_name']}**")
        left.caption(f"{LABELS[item['availability_type']]}{quantity}")

        if action.button("Edit", key=f"edit_{item['id']}"):
            st.session_state["editing_food_id"] = item["id"]
            st.rerun()

        if st.session_state.get("editing_food_id") == item["id"]:
            with st.form(f"edit_form_{item['id']}"):
                new_name = st.text_input("Food name", value=item["food_name"])
                new_type = st.selectbox(
                    "Availability",
                    ALLOWED_AVAILABILITY_TYPES,
                    index=ALLOWED_AVAILABILITY_TYPES.index(item["availability_type"]),
                    format_func=lambda value: LABELS[value],
                )
                new_quantity = st.number_input(
                    "Quantity", min_value=0.0, value=float(item["quantity"] or 0), step=0.1
                )
                new_unit = st.text_input("Unit", value=item["unit"] or "")
                save, cancel = st.columns(2)
                if save.form_submit_button("Save"):
                    try:
                        update_food(
                            food_id=item["id"],
                            food_name=new_name,
                            availability_type=new_type,
                            quantity=None if new_quantity == 0 else new_quantity,
                            unit=new_unit,
                        )
                        st.session_state.pop("editing_food_id", None)
                        st.rerun()
                    except (RuntimeError, ValueError) as exc:
                        st.error(str(exc))
                if cancel.form_submit_button("Cancel"):
                    st.session_state.pop("editing_food_id", None)
                    st.rerun()
        elif item["is_available"]:
            if st.button("Mark unavailable", key=f"off_{item['id']}"):
                set_food_availability(food_id=item["id"], is_available=False)
                st.rerun()
        else:
            if st.button("Mark available", key=f"on_{item['id']}"):
                set_food_availability(food_id=item["id"], is_available=True)
                st.rerun()


available_tab, unavailable_tab = st.tabs(["Available", "Unavailable"])

with available_tab:
    available = [item for item in foods if item["is_available"]]
    if not available:
        st.info("No foods are currently marked as available.")
    for item in available:
        render_food(item)

with unavailable_tab:
    unavailable = [item for item in foods if not item["is_available"]]
    if not unavailable:
        st.info("No unavailable foods.")
    for item in unavailable:
        render_food(item)
