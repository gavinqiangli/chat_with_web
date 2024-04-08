# chat_with_web
 
# some important notes in web_scrape.py
# need to define driver differently depending on local testing or cloud deployment

            # run Selenium with local brower for local test
            driver = webdriver.Chrome(options=options)

            # run Selenium on streamlit cloud, refer to https://selenium.streamlit.app/
            driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
