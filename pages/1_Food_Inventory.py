"""Food inventory page."""

from __future__ import annotations

import streamlit as st

from bulking_app.repositories.recipe_library import (
    COOKING_COMPLEXITIES, PREFERENCE_LEVELS, RECIPE_TYPES, delete_recipe,
    get_recipe, list_food_options, list_recipes, nutrition_per_weight, save_recipe,
)
from bulking_app.services.recipe_csv import import_recipe_csvs, template_csv

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


st.divider()
st.header("Recipe Library")
st.caption("Store recipes with recipe-level nutrition and manage the foods and quantities that make them up.")

try:
    recipes = list_recipes()
    food_options = list_food_options()
except RuntimeError as exc:
    st.error(str(exc))
    recipes, food_options = [], []

with st.expander("Add recipe", expanded=False):
    with st.form("add_recipe_form", clear_on_submit=True):
        recipe_name = st.text_input("Recipe name")
        recipe_type = st.selectbox("Type", RECIPE_TYPES)
        preference = st.selectbox("Preference", PREFERENCE_LEVELS)
        complexity = st.selectbox("Cooking complexity", COOKING_COMPLEXITIES)
        weight = st.number_input("Total prepared weight (g)", min_value=0.1, value=400.0)
        calories = st.number_input("Calories (kcal)", min_value=0.0, value=0.0)
        protein = st.number_input("Protein (g)", min_value=0.0, value=0.0)
        carbs = st.number_input("Carbohydrates (g)", min_value=0.0, value=0.0)
        fat = st.number_input("Fat (g)", min_value=0.0, value=0.0)
        food_by_name = {food["food_name"]: food for food in food_options}
        selected_foods = st.multiselect("Ingredients", list(food_by_name))
        ingredients = []
        for food_name in selected_foods:
            food = food_by_name[food_name]
            qty, unit = st.columns([2, 2])
            q = qty.number_input(f"{food['food_name']} quantity", min_value=0.0, value=100.0, key=f"add_qty_{food['id']}")
            u = unit.text_input(f"{food['food_name']} unit", value="g", key=f"add_unit_{food['id']}")
            ingredients.append({"food_id": food["id"], "quantity": q, "unit": u})
        if st.form_submit_button("Save recipe", type="primary"):
            try:
                save_recipe({"recipe_name": recipe_name, "recipe_type": recipe_type, "preference_level": preference,
                             "cooking_complexity": complexity, "total_weight_g": weight, "calories_kcal": calories,
                             "protein_g": protein, "carbohydrates_g": carbs, "fat_g": fat}, ingredients)
                st.success("Recipe saved.")
                st.rerun()
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

if not recipes:
    st.info("No recipes yet. Add a recipe or import the CSV templates below.")
for recipe in recipes:
    with st.container(border=True):
        st.markdown(f"**{recipe['recipe_name']}** · {recipe['recipe_type']} · {recipe['preference_level']} · {recipe['cooking_complexity']}")
        st.caption(f"Prepared weight: {recipe['total_weight_g']} g · {recipe['calories_kcal']} kcal · Protein {recipe['protein_g']} g · Carbs {recipe['carbohydrates_g']} g · Fat {recipe['fat_g']} g")
        detail = get_recipe(recipe["id"])
        if detail and detail["ingredients"]:
            st.write("Ingredients: " + ", ".join(f"{x['food_name']} — {x['quantity']} {x['unit']}" for x in detail["ingredients"]))
        serving = st.number_input("Nutrition for serving (g)", min_value=0.1, value=100.0, key=f"serving_{recipe['id']}")
        scaled = nutrition_per_weight(recipe, serving)
        st.caption(f"{serving:g} g serving: {scaled['calories_kcal']:.1f} kcal · Protein {scaled['protein_g']:.1f} g · Carbs {scaled['carbohydrates_g']:.1f} g · Fat {scaled['fat_g']:.1f} g")
        edit_col, delete_col = st.columns(2)
        if edit_col.button("Edit", key=f"recipe_edit_{recipe['id']}"):
            st.session_state["editing_recipe_id"] = recipe["id"]
        if delete_col.button("Delete", key=f"recipe_delete_{recipe['id']}"):
            try:
                delete_recipe(recipe["id"])
                st.rerun()
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
        if st.session_state.get("editing_recipe_id") == recipe["id"]:
            with st.form(f"edit_recipe_{recipe['id']}"):
                edited_name = st.text_input("Recipe name", value=recipe["recipe_name"])
                edited_type = st.selectbox("Type", RECIPE_TYPES, index=RECIPE_TYPES.index(recipe["recipe_type"]))
                edited_pref = st.selectbox("Preference", PREFERENCE_LEVELS, index=PREFERENCE_LEVELS.index(recipe["preference_level"]))
                edited_complexity = st.selectbox("Cooking complexity", COOKING_COMPLEXITIES, index=COOKING_COMPLEXITIES.index(recipe["cooking_complexity"]))
                edited_weight = st.number_input("Total prepared weight (g)", min_value=0.1, value=float(recipe["total_weight_g"]))
                edited_cal = st.number_input("Calories (kcal)", min_value=0.0, value=float(recipe["calories_kcal"]))
                edited_protein = st.number_input("Protein (g)", min_value=0.0, value=float(recipe["protein_g"]))
                edited_carbs = st.number_input("Carbohydrates (g)", min_value=0.0, value=float(recipe["carbohydrates_g"]))
                edited_fat = st.number_input("Fat (g)", min_value=0.0, value=float(recipe["fat_g"]))
                existing_ids = {item["food_id"] for item in detail["ingredients"]} if detail else set()
                food_by_name = {food["food_name"]: food for food in food_options}
                existing_foods = [item["food_name"] for item in detail["ingredients"]] if detail else []
                edited_foods = st.multiselect("Ingredients", list(food_by_name), default=existing_foods)
                edited_ingredients = []
                old_by_id = {item["food_id"]: item for item in detail["ingredients"]} if detail else {}
                for food_name in edited_foods:
                    food = food_by_name[food_name]
                    old = old_by_id.get(food["id"], {})
                    qty, unit = st.columns(2)
                    q = qty.number_input(f"{food['food_name']} quantity", min_value=0.0, value=float(old.get("quantity") or 100), key=f"edit_qty_{recipe['id']}_{food['id']}")
                    u = unit.text_input(f"{food['food_name']} unit", value=old.get("unit") or "g", key=f"edit_unit_{recipe['id']}_{food['id']}")
                    edited_ingredients.append({"food_id": food["id"], "quantity": q, "unit": u})
                if st.form_submit_button("Save changes"):
                    try:
                        save_recipe({"recipe_name": edited_name, "recipe_type": edited_type, "preference_level": edited_pref,
                                     "cooking_complexity": edited_complexity, "total_weight_g": edited_weight, "calories_kcal": edited_cal,
                                     "protein_g": edited_protein, "carbohydrates_g": edited_carbs, "fat_g": edited_fat},
                                    edited_ingredients, recipe_id=recipe["id"])
                        st.session_state.pop("editing_recipe_id", None)
                        st.rerun()
                    except (RuntimeError, ValueError) as exc:
                        st.error(str(exc))

with st.expander("CSV import and templates", expanded=False):
    st.write("Upload both files together. Recipe names already in the library are updated, and their ingredient lists are replaced by the CSV definition.")
    st.download_button("Download Recipe Template", template_csv("recipes"), "recipes_template.csv", "text/csv")
    st.download_button("Download Recipe Ingredients Template", template_csv("ingredients"), "recipe_ingredients_template.csv", "text/csv")
    recipe_file = st.file_uploader("recipes.csv", type=["csv"], key="recipes_csv")
    ingredient_file = st.file_uploader("recipe_ingredients.csv", type=["csv"], key="recipe_ingredients_csv")
    if recipe_file and ingredient_file:
        if st.button("Validate and preview CSV files"):
            try:
                from bulking_app.services.recipe_csv import parse_and_validate
                preview, ingredient_preview = parse_and_validate(recipe_file, ingredient_file, {x["food_name"] for x in food_options})
                st.session_state["recipe_import_preview"] = (recipe_file.getvalue(), ingredient_file.getvalue(), len(preview), len(ingredient_preview))
                st.success(f"Validated {len(preview)} recipes and {len(ingredient_preview)} ingredient rows.")
                st.dataframe(preview, use_container_width=True)
            except (RuntimeError, ValueError, UnicodeDecodeError) as exc:
                st.error(str(exc))
    if "recipe_import_preview" in st.session_state:
        _, _, n_recipes, n_ingredients = st.session_state["recipe_import_preview"]
        st.caption(f"Ready to import {n_recipes} recipes and {n_ingredients} ingredient rows.")
        if st.button("Import validated CSV", type="primary"):
            data = st.session_state.pop("recipe_import_preview")
            try:
                result = import_recipe_csvs(data[0], data[1])
                st.success(f"Imported {result['recipes']} recipes and {result['ingredients']} ingredients.")
                st.rerun()
            except (RuntimeError, ValueError, UnicodeDecodeError) as exc:
                st.error(str(exc))

