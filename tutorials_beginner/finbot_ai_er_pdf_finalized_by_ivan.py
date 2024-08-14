import os
import autogen
from textwrap import dedent
from finrobot.utils import register_keys_from_json
from finrobot.agents.workflow import SingleAssistantShadow
from openai import OpenAI

def generate_report(stock_symbol, date, house_view, entry_price, target_price, stop_loss):

    """
    Generates a financial report for a given stock symbol.

    Parameters:
    stock_symbol (str): The symbol of the stock.
    date (str): The date for which the report is generated.
    house_view (str): The house view or opinion on the stock. Buy/Sell/Neutral
    entry_price (float): The entry price of the stock.
    target_price (float): The target price of the stock.
    stop_loss (float): The stop loss price of the stock.

    """

    llm_config = {
        "config_list": autogen.config_list_from_json(
            "../OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-4o-mini"],
            },
        ),
        "timeout": 120,
        "temperature": 0.5,
    }
    register_keys_from_json("../config_api_keys")

    # Intermediate results will be saved in this directory
    work_dir = "../report"
    os.makedirs(work_dir, exist_ok=True)

    assistant = SingleAssistantShadow(
        "Expert_Investor",
        llm_config,
        max_consecutive_auto_reply=None
    )

    text =     f"""
        With the files in directory you've been provided, retrieve {stock_symbol}'s files up to {date} and analyze financial data.
        Pay attention to the followings:
        - Do not compile annual report.
        - Explicitly explain your working plan before you kick off.
        - Use tools one by one for clarity, especially when asking for instructions. 
        - All your file operations should be done in "{work_dir}". 
        - Display any image in the chat once generated.
        - Terminate the conversation automatically when you finish your tasks.
        - Exit the chat when you are done.
    """
    message = dedent(text
    )

    assistant.chat(message, use_cache=True, max_turns=50,
                summary_method="last_msg")

    # Place your openai api key
    client = OpenAI(api_key="openai api key", base_url="https://api.openai.com:10443/v1")
    work_dir = "../report"
    summaries = []
    print()
    print('Generating summaries...')

    for filename in os.listdir(work_dir):
        file_path = os.path.join(work_dir, filename)
        if os.path.isfile(file_path) and not filename.lower().endswith('.png'):
            with open(file_path, 'r') as file:
                file_content = file.read()
            
            # Use the OpenAI API to generate a summary of the content
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": dedent(
                        """
                        Role: Expert Investor
                        Department: Finance
                        Primary Responsibility: Summarization of Customized Financial Analysis Documents

                        Role Description:
                        As an Expert Investor within the finance domain, your expertise is harnessed to summarise Financial Analysis documents that cater to specific client requirements. This role demands a deep dive into financial statements and market data to unearth insights regarding a company's financial performance and stability. Engaging directly with clients to gather essential information and continuously refining the report with their feedback ensures the final product precisely meets their needs and expectations.

                        Key Objectives:

                        Analytical Precision: Employ meticulous analytical prowess to interpret financial data, identifying underlying trends and anomalies.
                        Effective Communication: Simplify and effectively convey complex financial narratives, making them accessible and actionable to non-specialist audiences.
                        Client Focus: Dynamically tailor reports in response to client feedback, ensuring the final analysis aligns with their strategic objectives.
                        Adherence to Excellence: Maintain the highest standards of quality and integrity in report generation, following established benchmarks for analytical rigor.
                        Performance Indicators:
                        The efficacy of the Financial Analysis Summarization is measured by its utility in providing clear, actionable insights. This encompasses aiding corporate decision-making, pinpointing areas for operational enhancement, and offering a lucid evaluation of the company's financial health. Success is ultimately reflected in the report's contribution to informed investment decisions and strategic planning.

                        Reply TERMINATE when everything is settled.
                        """)},
                    {"role": "user", "content": f"Summarize the following content. The length of the summary should be around 120 words:\n\n{file_content}"},
                ],
            )

            summary = completion.choices[0].message.content
            summaries.append(f"Summary for {filename}:\n{summary}\n")

    combined_summaries = "\n".join(summaries)

    output_file_path = f"{stock_symbol} equity research report.txt"
    with open(output_file_path, 'w') as output_file:
        output_file.write(combined_summaries)

    title_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful expert investor."},
            {"role": "user", 
            "content": 
            f"Generate a title (about 20 words) for the following summary for the stock {stock_symbol}:\n\n{combined_summaries} and generate a short paragraph (about 20 words) to combine the equity research summary with the house view {house_view} entry price: {entry_price} target price: {target_price} stop loss: {stop_loss}"            
            },
        ],
    )

    title = title_completion.choices[0].message.content
    with open(output_file_path, 'a') as output_file:
        output_file.write(f"\nTitle: {title}\n")

    print(f"Summaries and title have been written to {output_file_path}")

if __name__ == "__main__":
    generate_report('msft US','2024-08-13','Buy',110, 150 , 85)