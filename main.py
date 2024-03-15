import requests
import time
from bs4 import BeautifulSoup

URL = "https://www.tiobe.com/tiobe-index/"


def get_top_10_languages(soup):
    # Find the table with id 'top20'
    top20_table = soup.find('table', id='top20')

    # Initialize the list to collect top 10 languages
    top_10 = []

    if top20_table:
        # Extract the top 10 languages
        for row in top20_table.find_all('tr')[1:11]:  # skip the header row
            cols = row.find_all('td')
            if cols:
                language_info = {
                    'name': cols[4].text.strip(),
                    'place': cols[0].text.strip(),
                    'prev_year_place': cols[1].text.strip(),
                    'highest_place': 'No data'  # Default value if no historical data is available
                }
                top_10.append(language_info)
    
    # Find the table with id 'VLTH' which has the historical data
    vlth_table = soup.find('table', id='VLTH')

    if vlth_table:
        # Update the highest ranking position in top 10 languages
        for language in top_10:
            for hist_row in vlth_table.find_all('tr'):
                hist_cols = hist_row.find_all('td')
                if hist_cols and language['name'].lower() in hist_cols[0].text.lower():
                    # Extract positions, ignoring non-numeric entries
                    positions = [col.text.strip() for col in hist_cols[1:] if col.text.strip().isdigit()]
                    if positions:
                        # Convert all positions to integers and find the minimum which will be the highest place
                        language['highest_place'] = min(map(int, positions))
                    break

    return top_10


def generate_main_page():
    content = """
# Witaj na mojej stronie o językach programowania! :)

Na tej stronie znajdziesz listę **najbardziej popularnych języków programowania** na dzień dzisiejszy. Lista została zebrana i zaktualizowana dzięki danym ze strony [tiobe](https://www.tiobe.com/tiobe-index/).

Dla każdego języka programowania przygotowałem:
- kilka informacji,
- wyniki wyszukiwania z DuckDuckGo, abyś mógł poznać, co świat myśli o danym języku.

Przejdź do [listy języków programowania](./list.md), aby odkryć więcej!
    """.strip()

    with open('index.md', 'w', encoding='utf-8') as file:
        file.write(content)


def generate_list_page(soup):
    top_10_languages = get_top_10_languages(soup)
    content = "# Top 10 Programming Languages\n\n"
    content += "Here are the top 10 programming languages as ranked by the TIOBE index, along with some additional details:\n\n"

    for i, language in enumerate(top_10_languages, start=1):
        # DuckDuckGo search URL for insights
        duck_link = f"https://duckduckgo.com/?q={language['name'].replace(' ', '+')}+programming+language"
        
        content += f"## {i}. {language['name']}\n\n"
        content += f"- Current Rank: {language['place']}\n"
        content += f"- Previous Year Rank: {language['prev_year_place']}\n"
        
        highest_place = language['highest_place']
        highest_place_text = "No data" if highest_place == 'No data' else f"#{highest_place}"
        content += f"- Highest Ranking Ever: {highest_place_text}\n"

        if language['name'] == 'C#':
            language['name'] = 'C_sharp'

        if language['name'] == 'Visual Basic':
            language['name'] = 'Visual_Basic'
        
        # Add a line for DuckDuckGo insights with a hyperlink
        content += f"- DuckDuckGo Insights: [What does DuckDuckGo say about {language['name']}?](./{language['name']}_duck.md)\n\n"

    with open('list.md', 'w', encoding='utf-8') as file:
        file.write(content)

    return top_10_languages


def make_request_with_retries(url, headers=None, max_retries=5):
    retries = 0
    backoff_factor = 1  # Starts with 1 second

    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()  # Assuming the API returns JSON content
        except requests.exceptions.HTTPError as err:
            if 500 <= err.response.status_code < 600:
                # Retry for server-side errors
                retries += 1
                wait_time = backoff_factor * (2 ** retries)
                print(f"Server error occurred, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Break the loop if the error is not server-side
                break
        except requests.exceptions.RequestException as e:
            # For other types of exceptions like connection error, timeout, etc., we may want to retry
            retries += 1
            wait_time = backoff_factor * (2 ** retries)
            print(f"Request failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # If the loop exits without returning, it means all retries have been exhausted
    print("All retries have been exhausted.")
    return None


def generate_duck_page(language_name):
    # If the language is C#, replace it with C sharp for the API call
    if language_name == 'C#':
        query_name = 'C sharp'
    else:
        query_name = language_name
    
    # DuckDuckGo API URL
    api_url = f"https://api.duckduckgo.com/?q={query_name}+programming+language&format=json&pretty=1"

    # Make a request with retries
    data = make_request_with_retries(api_url)

    if data is None:
        return
    
    # Extract relevant information from the response
    Abstract = data.get('Abstract', 'No abstract provided.')
    RelatedTopics = data.get('RelatedTopics', [])
    
    # Start building the content for the Markdown file
    content = f"# {language_name} - Insights from DuckDuckGo\n\n"
    content += f"## Abstract\n\n{Abstract}\n\n"
    
    # Add related topics to the content
    content += "## Related Topics\n\n"
    for topic in RelatedTopics:
        if 'Text' in topic:
            content += f"- {topic['Text']}\n"
    
    # Write the content to a Markdown file
    file_name = f"{language_name.replace(' ', '_')}_duck.md"

    if file_name == 'C#_duck.md':
        file_name = 'C_sharp_duck.md'

    if file_name == 'Visual Basic_duck.md':
        file_name = 'Visual_Basic_duck.md'

    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(content)


def generate_duck_pages(top_10_languages):
    for language in top_10_languages:
        print(language)
        generate_duck_page(language['name'])


def main():
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    generate_main_page()
    top_10_languages = generate_list_page(soup)
    generate_duck_pages(top_10_languages)


if __name__ == '__main__':
    main()
    print("Main done so everything works fine")
