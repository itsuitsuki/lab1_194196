from typing import Dict, List
from autogen import ConversableAgent
import sys
import os

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # DONE
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    
    # Implementation
    # read restaurant-data.txt
    with open("restaurant-data.txt", "r") as f:
        lines = f.readlines()
    # find the restaurant name
    comments_wrt_name = [line.split(". ")[1] for line in lines if restaurant_name in line.split(". ")[0]] # "xxx. YYYY(comment)"
    return {restaurant_name: comments_wrt_name}
    


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # DONE
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.04}
    # NOTE: be sure to round the score to 2 decimal places.
    def before_sqrt(food_score: int, customer_service_score: int) -> float:
        return food_score**2 * customer_service_score
    N = len(food_scores)
    multiplier = 1/(N * (125)**0.5) * 10
    sqrt_list = [before_sqrt(food_score, customer_service_score)**0.5 for food_score, customer_service_score in zip(food_scores, customer_service_scores)]
    overall_score = sum(sqrt_list) * multiplier
    return {restaurant_name: round(overall_score, 2)} # FIXME: round may be too cursed

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    pass

# TODO: feel free to write as many additional functions as you'd like.

# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = "" # TODO
    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config)
    entrypoint_agent.register_for_llm(name="fetch_reviews_for_restaurant", description="Fetches the reviews for a specific restaurant.")(fetch_reviews_for_restaurant)
    entrypoint_agent.register_for_execution(name="fetch_reviews_for_restaurant")(fetch_reviews_for_restaurant)

    # DONE
    # Create more agents here. 
    
    
    # TODO
    # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # Uncomment once you initiate the chat with at least one agent.
    # result = entrypoint_agent.initiate_chats([{}])
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])