import gradio as gr
import pandas as pd

def maximize_nutritional_value_dp(values, gis, chos, prices, gl_limit, budget_limit):
    n = len(values)  # Number of food items

    # Define scale factor for precision, if we don't use scale here, the gls cannot be used as index in dp array
    scale_factor = 10

    # Calculate scaled GL values with proper rounding
    gls = [int(round(gis[i] * chos[i] * scale_factor / 100)) for i in range(n)]
    gl_limit_scaled = int(gl_limit * scale_factor)  # Scale GL limit

    # Initialize DP array with negative infinity
    dp = [[float('-inf')] * (budget_limit + 1) for _ in range(gl_limit_scaled + 1)]
    dp[0][0] = 0  # Base case

    # Dynamic programming computation
    for i in range(n):
        for j in range(gl_limit_scaled, gls[i] - 1, -1):  # GL constraint
            for k in range(budget_limit, prices[i] - 1, -1):  # Budget constraint
                if dp[j - gls[i]][k - prices[i]] != float('-inf'):
                    dp[j][k] = max(dp[j][k], dp[j - gls[i]][k - prices[i]] + values[i])

    # Find the maximum nutritional value and its position
    max_value = float('-inf')
    final_j, final_k = 0, 0
    for j in range(gl_limit_scaled + 1):
        for k in range(budget_limit + 1):
            if dp[j][k] > max_value:
                max_value = dp[j][k]
                final_j, final_k = j, k

    # Backtracking to find selected items
    selected_items = []
    j, k = final_j, final_k
    for i in range(n - 1, -1, -1):
        if j >= gls[i] and k >= prices[i]:
            if dp[j][k] == dp[j - gls[i]][k - prices[i]] + values[i]:
                selected_items.append(i)
                j -= gls[i]
                k -= prices[i]

    # Return maximum nutritional value and selected item indices
    return max_value, selected_items[::-1]

def optimize_menu(food_data, gl_limit, budget_limit):
    # Extract data from DataFrame
    food_names = food_data['Food Name'].tolist()
    values = food_data['Nutritional Value'].tolist()
    gis = food_data['GI Value'].tolist()
    chos = food_data['Carbohydrate Content'].tolist()
    prices = food_data['Price'].tolist()

    max_value, selected_indices = maximize_nutritional_value_dp(
        values, gis, chos, prices, gl_limit, budget_limit
    )

    selected_foods = food_data.iloc[selected_indices]

    result_text = f"Maximum Nutritional Value: {max_value}"
    return result_text, selected_foods

def add_food_item(food_data, food_name, value, gi, cho, price):
    new_food = pd.DataFrame({
        'Food Name': [food_name],
        'Nutritional Value': [value],
        'GI Value': [gi],
        'Carbohydrate Content': [cho],
        'Price': [price]
    })
    updated_food_data = pd.concat([food_data, new_food], ignore_index=True)
    return updated_food_data

def delete_food_items(food_data, items_to_delete):
    # Filter out the items to delete
    updated_food_data = food_data[~food_data['Food Name'].isin(items_to_delete)].reset_index(drop=True)
    return updated_food_data

# Initial food data
food_data = pd.DataFrame({
    'Food Name': ["Apple", "Banana", "Carrot", "Pear"],
    'Nutritional Value': [10, 20, 30, 40],
    'GI Value': [50, 60, 40, 30],
    'Carbohydrate Content': [15, 20, 10, 5],
    'Price': [5, 10, 8, 7]
})

with gr.Blocks() as demo:
    gr.Markdown("# Nutritional Menu Optimizer")
    gr.Markdown("Input food items and their parameters, set GL and budget limits, and find the optimal menu.")

    with gr.Tab("Add/Delete Food Items"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Add Food Item")
                food_name = gr.Textbox(label="Food Name")
                value = gr.Number(label="Nutritional Value", value=0)
                gi = gr.Number(label="GI Value", value=0)
                cho = gr.Number(label="Carbohydrate Content", value=0)
                price = gr.Number(label="Price", value=0)
                add_button = gr.Button("Add Food Item")
            with gr.Column():
                gr.Markdown("### Delete Food Items")
                delete_items = gr.Dropdown(label="Select Food Items to Delete", choices=food_data['Food Name'].tolist(), multiselect=True)
                delete_button = gr.Button("Delete Selected Items")
        food_data_display = gr.DataFrame(value=food_data, label="Food Items")

    with gr.Tab("Optimize Menu"):
        gl_limit = gr.Number(label="GL Limit", value=50)
        budget_limit = gr.Number(label="Budget Limit", value=30)
        optimize_button = gr.Button("Optimize")
        result_text = gr.Textbox(label="Result")
        selected_foods_display = gr.DataFrame(label="Selected Food Items")

    # Function to update food data when adding a new item
    def update_food_data_add(food_data_display, food_name, value, gi, cho, price):
        updated_food_data = add_food_item(food_data_display, food_name, value, gi, cho, price)
        return gr.update(value=updated_food_data), gr.update(choices=updated_food_data['Food Name'].tolist())

    # Function to update food data when deleting items
    def update_food_data_delete(food_data_display, delete_items):
        updated_food_data = delete_food_items(food_data_display, delete_items)
        return gr.update(value=updated_food_data), gr.update(choices=updated_food_data['Food Name'].tolist())

    add_button.click(
        update_food_data_add,
        inputs=[food_data_display, food_name, value, gi, cho, price],
        outputs=[food_data_display, delete_items]
    )

    delete_button.click(
        update_food_data_delete,
        inputs=[food_data_display, delete_items],
        outputs=[food_data_display, delete_items]
    )

    optimize_button.click(
        optimize_menu,
        inputs=[food_data_display, gl_limit, budget_limit],
        outputs=[result_text, selected_foods_display]
    )

# 端口 80
demo.launch(server_port=80)