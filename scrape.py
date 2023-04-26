"""
Extract faculty or staff information from web pages

Read the SJSU faculty index web page at https://sjsu.edu/people/.
Extract information about each faculty or staff from links on index page
Save the information in the csv file specified.
"""
import urllib.request
import urllib.error
import urllib.robotparser
import urllib.parse
import bs4
import re
import sys
import os


def read_url(url):
    """
    Open the given url and return the corresponding soup object.
    :param url:(string) - the address of the web page to be read
    :return: (Beautiful Soup object) corresponding Beautiful Soup
    object or None if an error is encountered.
    """
    try:
        with urllib.request.urlopen(url) as url_file:
            url_bytes = url_file.read()
    except urllib.error.URLError as url_err:
        print(f'Error opening url: {url}\n{url_err}')
    except Exception as other_err:  # safer on the web
        print(f'Other error with url: {url}\n{other_err}')
    else:
        soup = bs4.BeautifulSoup(url_bytes, 'html.parser')
        return soup


def get_people_links(url):
    """
    Read the given url and return the relevant referenced links.
    :param url:(string) - the address of the faculty index page
    :return: (list of strings) - the relevant people links
    """
    soup = read_url(url)
    if soup is not None:
        base = 'https://sjsu.edu/'
        regex = re.compile(r'/people/', re.IGNORECASE)
        links = [urllib.parse.urljoin(base, anchor.get('href', None)) for
                 anchor in soup('a', href=regex)]
        return links


def extract_name(soup):
    """
    Extract the first and last name from the soup object
    :param soup: (Beautiful Soup object) representing the faculty/staff
                web page
    :return: a tuple of strings representing the first and last names
    """
    h1 = soup('h1')
    if h1:
        name = h1[0].get_text().strip()
        if ',' in name:
            return name.split(',')[0], name.split(',')[1]
        elif len(name.split()) > 1:
            return name.split()[-1], name.split()[0]
    else:
        return ""


def extract_email(soup):
    """
    Extract the email address from the soup object
    :param soup: (Beautiful Soup object) representing the faculty/staff
                web page
    :return: a string representing the email address
    """
    email_pattern = r'\S+@\S+\.\S+'
    regex = re.compile(email_pattern)
    email = soup.find(string=regex)
    if email:
        email_match = re.search(email_pattern, email)
        if email_match:
            return email_match.group(0).strip(",")
        else:
            return ""
    else:
        return ""


def extract_phone(soup):
    """
    Extract the phone number from the soup object
    :param soup: (Beautiful Soup object) representing the faculty/staff
                web page
    :return: a string representing the phone number
    """
    regex = re.compile(r'(^phone$|^telephone$|^telephone:$)', re.IGNORECASE)
    phone = soup.find(string=regex)
    if phone:
        format1 = phone.get_text()
        format2 = phone.find_next().get_text()
        phone_pattern = r'\(?\d{3}\)?[ -.]?\/?\d{3}[ ]?[ -.]?[ ]?\d{4}'
        phone_match = re.search(phone_pattern, format1 + format2)
        if phone_match:
            return phone_match.group(0)
        else:
            return ""
    else:
        return ""


def extract_education(soup):
    """
    Extract the education blurb from the soup object
    :param soup: (Beautiful Soup object) representing the faculty/staff
                web page
    :return: a string representing the education blurb
    """
    education = soup.find('h2', string='Education')
    if education:
        next_element = education.find_next()
        if next_element.name == 'ul':
            return next_element.find_next().get_text()\
                .replace(',', '-').replace('\n', ' ').strip()
        else:
            return next_element.get_text().replace(',', '-') \
                    .replace('\n', ' ').strip()
    else:
        return ""


def get_info(url):
    """
    Extract the information from a single faculty/staff web page
    :param url: (string) the address of the faculty/staff web page
    :return: a comma separated string containing: the last name,
    first name, email, phone and education
    """
    soup = read_url(url)
    if soup is not None:
        name = extract_name(soup)
        if name:
            last_name, first_name = extract_name(soup)
            return f'{last_name.strip()},{first_name.strip()},' \
                   f'{extract_email(soup).strip()},' \
                   f'{extract_phone(soup).strip()},' \
                   f'{extract_education(soup).strip()}'


def ok_to_crawl(url):
    """
    Check if it is polite to crawl the specified absolute url.
    :param url: (string) absolute url that we would like to crawl
    :return: (Boolean) True if we successfully read the
        corresponding robots.txt and determined that our user-agent
        is allowed to crawl this url.
        False if the user agent is not allowed to crawl it or there
        was an error reading robots.txt
    """
    parsed_url = urllib.parse.urlparse(url)
    if not parsed_url.scheme or not parsed_url.hostname:
        print('Not a valid absolute url: ', url)
        return False

    # Build the corresponding robots.txt url name
    robot = urllib.parse.urljoin(
        f'{parsed_url.scheme}://{parsed_url.hostname}', '/robots.txt')
    user_agent = urllib.request.URLopener.version  # our user-agent
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robot)
    try:
        rp.read()
    except urllib.error.URLError as url_err:
        print(f'Error opening robot.txt for url {url}\n{url_err}')
        return False
    else:
        return rp.can_fetch(user_agent, url)


def harvest(url, filename):
    """
    Harvest the information starting from the url specified and write
    that information to the file specified.
    :param url: (string)the main faculty index url
    :param filename: (string) name of the output csv file
    :return: None
    """
    people_links = get_people_links(url)
    with open(filename, 'w', encoding='utf-8') as output_file:
        output_file.write('Last Name,First Name,Email,'
                          'Phone Number,Education \n')
        for i in range(1, len(people_links)):
            info = get_info(people_links[i])
            if info is not None:
                output_file.write(f'{info}\n')


def main():
    if len(sys.argv) != 2:
        print("Error: invalid number of arguments")
        print("Usage: scrape.py filename")
    elif not os.path.splitext(sys.argv[1])[1] == '.csv':
        print("Please specify a csv filename")
    else:
        url = "https://sjsu.edu/people/"
        if ok_to_crawl(url):
            harvest(url, sys.argv[1])
        else:
            print("This URL cannot be fetched!")


if __name__ == '__main__':
    main()


