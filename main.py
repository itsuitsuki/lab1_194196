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
    # TODO: May need to retrieve the restaurant name from similarity instead of exact match
    
    comments_wrt_name = [". ".join(line.split(". ")[1:]) for line in lines if restaurant_name in line.split(
        ". ")[0]]  # "xxx. YYYY(comment)"
    return {restaurant_name: comments_wrt_name}


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # DONE
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service.
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to round the score to 3 decimal places.
    def before_sqrt(food_score: int, customer_service_score: int) -> float:
        return food_score**2 * customer_service_score
    N = len(food_scores)
    multiplier = 1/(N * (125)**0.5) * 10
    sqrt_list = [before_sqrt(food_score, customer_service_score)**0.5 for food_score,
                 customer_service_score in zip(food_scores, customer_service_scores)]
    overall_score = sum(sqrt_list) * multiplier
    # FIXME: round may be too cursed
    # in the return, the float should be strictly 3 decimal places, can't be 10.0 but must be 10.000
    return {restaurant_name: round(overall_score, 3)}


def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # DONE
    # It may help to organize messages/prompts within a function which returns a string.
    # For example, you could use this function to return a prompt for the data fetch agent
    # to use to fetch reviews for a specific restaurant.

    # NOTE: Prompt here is a message from the entrypoint agent to the data fetch agent.
    with open("restaurant-data.txt", "r") as f:
        lines = f.readlines()
    # find the restaurant names
    restaurant_names = [line.split(". ")[0] for line in lines]
    set_restaurant_names = set(restaurant_names)
    
    prompt_1 = f"Please fetch the reviews for the restaurant mentioned in the query: {restaurant_query}.\n\
            What you could help me with is to give an argument to the function fetch_restaurant_data, which is the restaurant name.\n\
            The function will return the reviews for that restaurant, so we can help the user to exactly know what they are looking for."
    prompt_2 = f"Here is a list of restaurant names that you can choose one match from:\n{', '.join(set_restaurant_names)}\n\
            Please make sure to return the reviews for the restaurant that exactly matches the query, and also make sure the name is exactly the same as one in the list."
    return prompt_1 + prompt_2


def get_review_analysis_agent_prompt(reviews_dict: Dict[str, List[str]]) -> str:
    rest_name = list(reviews_dict.keys())[0]
    review_list = reviews_dict[rest_name]
    # make review list like this:
    # "1. review1\n2. review2\n3. review3\n..."
    review_list_str = "\n".join(
        [f"{i+1}. {review}" for i, review in enumerate(review_list)])

    prompt_1 = """
    As a helpful agent, you should be able to analyze the reviews of a restaurant and return the food and customer service scores, for **each review**.
    This is to say, the correspondence is one-to-one. Each review has a food score and a customer service score.
    
    You should extract these two scores by looking for keywords in each review. Each review has keyword adjectives that correspond to the score that the restaurant should get for its `food_score` and `customer_service_score`. Here are the keywords the agent should look out for:

    - Score 1/5 has one of these adjectives: awful, horrible, or disgusting.
    - Score 2/5 has one of these adjectives: bad, unpleasant, or offensive.
    - Score 3/5 has one of these adjectives: average, uninspiring, or forgettable.
    - Score 4/5 has one of these adjectives: good, enjoyable, or satisfying.
    - Score 5/5 has one of these adjectives: awesome, incredible, or amazing.

    Each review will have exactly only two of these keywords (adjective describing food and adjective describing customer service), and the score (N/5) is only determined through the above listed keywords. No other factors go into score extraction. To illustrate the concept of scoring better, here's an example review. 

    > The food at McDonald's was average, but the customer service was unpleasant. The uninspiring menu options were served quickly, but the staff seemed disinterested and unhelpful.

    We see that the food is described as "average", which corresponds to a `food_score` of 3. We also notice that the customer service is described as "unpleasant", which corresponds to a `customer_service_score` of 2. Therefore, the agent should be able to determine `food_score: 3` and `customer_service_score: 2` for this example review.
    """
    prompt_2 = """
    Here is an example of one input:
    
    ```
    1. The food at Taco Bell was bad, with flavors that seemed artificial. The customer service was average, neither particularly helpful nor rude.

    2. The food at Taco Bell was bad, with questionable quality and taste. The customer service was uninspiring, neither terrible nor impressive.
    
    3. The food is awful, with a taste that is unpalatable. The customer service was bad, with staff that seemed uninterested and unhelpful.
    
    4. Pretty good food, with a taste that is enjoyable. The customer service was good, with staff that seemed helpful and attentive.
    ```
    As an agent, you should be able to extract the food and customer service scores for each review. 
    The output should be a list of dictionaries, where each dictionary corresponds to a review having the keys `food_score` and `customer_service_score`.
    The output for the above example should be:
    ```json
    [
        {"food_score": 2, "customer_service_score": 3}, // review 1
        {"food_score": 2, "customer_service_score": 3}, // review 2
        {"food_score": 1, "customer_service_score": 2}, // review 3
        {"food_score": 4, "customer_service_score": 4}, // review 4
    ]
    ```
    """
    prompt_3 = f"""
    Now, after you see this example, please match the adjectives in the reviews to the scores and return the scores for each review.
    Here is the list of reviews for the restaurant {rest_name}:\n
    {review_list_str}
    """
    return prompt_1 + prompt_2 + prompt_3

def get_scoring_agent_prompt(restaurant_name: str, content_str_with_scores: str) -> str:
    prompt_1 = f"""
    As a scoring agent, you should calculate the overall score for a restaurant based on the food and customer service scores for each review.
    You will receive a string with a piece of stringified list of dictionaries, where each dictionary corresponds to a review having the keys `food_score` and `customer_service_score`.
    And you should return the resturant name which is {restaurant_name}, the list of food scores and the list of customer service scores,
    as the arguments to the function `calculate_overall_score`. The function will return the overall score for the restaurant, so that we can help the user to know how good the restaurant is.\n\n"""
    prompt_2 = """
    Here is an example of one input:
    ----------------
    <Other outputs>
    ```json
    [
        {"food_score": 2, "customer_service_score": 3}, // review 1
        {"food_score": 2, "customer_service_score": 3}, // review 2
        {"food_score": 1, "customer_service_score": 2}, // review 3
        {"food_score": 4, "customer_service_score": 4}, // review 4
    ]
    ```
    <Other outputs>
    ----------------
    
    As a scoring agent, you should be able to extract the two lists, which should be ordered in the same way as the reviews:
    `food_scores = [2, 2, 1, 4]` and `customer_service_scores = [3, 3, 2, 4]`.
    The final result should be `restaurant_name`, `food_scores`, and `customer_service_scores` as the arguments to the function `calculate_overall_score`.
    """
    prompt_3 = f"""
    Now, after you see this example, please extract the food and customer service scores for each review and return the scores for the restaurant {restaurant_name}.
    The string with the piece of stringified list of dictionaries is as follows:
    {content_str_with_scores}
    """
    return prompt_1 + prompt_2 + prompt_3


# Do not modify the signature of the "main" function.
def main(user_query: str):
    VERBOSE = False
    # NOTE: agent.register_for_llm is used to register function call arguments
    # NOTE: agent.register_for_execution is used to let the agent execute the function! (not just suggest it)
    entrypoint_agent_system_message = "You work as a powerful and strong agent who helps other agent implement and work on their tasks. You are the entrypoint agent, and you are responsible for managing the other agents."
    data_fetch_agent_system_message = "You are a clever summarizer that takes in a query and returns the restaurant name.\
        You are responsible for taking in a query from the user and returning a restaurant name as the argument to the fetch_restaurant_data function."
    review_analysis_agent_system_message = "You are a smart and professional analyzer that takes in the reviews of a restaurant and returns the overall score.\
        Note that you are responsible for capturing every detail in every review, and generating scores in different dimensions for the restaurant."
    scoring_agent_system_message = "You are an agent that is excellent at processing stringified structured data.\
        You are responsible for taking in a string with a piece of stringified list of dictionaries, and output as what the calculate_overall_score function expects to receive."
    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [
        {"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}



    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent",
                                        system_message=entrypoint_agent_system_message,
                                        llm_config=llm_config)
    data_fetch_agent = ConversableAgent("data_fetch_agent",
                                        system_message=data_fetch_agent_system_message,
                                        llm_config=llm_config)  # NOTE: User query -> restaurant name
    review_analysis_agent = ConversableAgent("review_analysis_agent",
                                             system_message=review_analysis_agent_system_message,
                                             llm_config=llm_config)  # NOTE: Reviews -> scores
    scoring_agent = ConversableAgent("scoring_agent",
                                     system_message=scoring_agent_system_message,
                                     llm_config=llm_config)  # NOTE: Scores -> overall score

    # NOTE: EVERYTHING is handed to the entrypoint agent to execute. Other agents work as argument advisors.
    # 1. Query to restaurant name agent
    entrypoint_agent.register_for_execution(
        name="fetch_restaurant_data")(fetch_restaurant_data)
    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="This fetches the restaurant data. It takes in a restaurant name and returns the reviews for that restaurant\
                                                    The output is a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.")(fetch_restaurant_data)
    result = entrypoint_agent.initiate_chat(silent=not VERBOSE,
        recipient=data_fetch_agent, message=get_data_fetch_agent_prompt(user_query), max_turns=2)
    data_fetch_dict_str = result.chat_history[-2]['content']

    # 2. Query to review analysis agent, which take in the reviews and return list of two scores
    import json
    # str to dict
    data_fetch_dict = json.loads(data_fetch_dict_str)
    rest_name = list(data_fetch_dict.keys())[0]
    get_review_analysis_agent_prompt(data_fetch_dict)
    # directly initiate chat with review analysis agent
    result = entrypoint_agent.initiate_chat(silent=not VERBOSE,
        recipient=review_analysis_agent, message=get_review_analysis_agent_prompt(data_fetch_dict), max_turns=1)
    content_str_with_scores = result.chat_history[1]['content']
    
    # 3. Query to scoring agent, which take in the scores and return the overall score
    entrypoint_agent.register_for_execution(
        name="calculate_overall_score")(calculate_overall_score)
    scoring_agent.register_for_llm(name="calculate_overall_score", description="This calculates the overall score for a restaurant based on the food and customer service scores for each review.\
                                                    This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5.\
                                                    The output is a dictionary with the key being the restaurant name and the value being the overall score for that restaurant.")(calculate_overall_score)
    result = entrypoint_agent.initiate_chat(silent=not VERBOSE,
        recipient=scoring_agent, message=get_scoring_agent_prompt(rest_name, content_str_with_scores), max_turns=2)
    overall_score = result.chat_history[-2]['content']
    overall_score_dict = json.loads(overall_score)
    print("%.3f" % (overall_score_dict[rest_name]))
    

# DO NOT modify this code below.
if __name__ == "__main__": 
    assert len(
        sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])
