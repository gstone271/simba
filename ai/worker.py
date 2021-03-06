#!/usr/bin/env python

# For selenium to work you will need to install the selenium
# Python package as well as a webdriver executable. Follow the
# installation instructions at https://pypi.org/project/selenium/

import sys
import os
import os.path
import re
import selenium
from urllib3.exceptions import HTTPError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException

def run_browser(simbaSettings, displayPage=False): #Runs the chrome browser
    baseDir = os.path.abspath(os.path.join(sys.path[0], os.pardir))
    with open(os.path.join(baseDir, "bot.js")) as f:
        botJs = f.read()
    botJs += f"\n; importSaveDecompressed('{simbaSettings}');"
    options = webdriver.ChromeOptions()
    options.add_argument('disable-web-security')
    if not displayPage:
        options.add_argument('headless')
    driver = None
    try:
        driver = webdriver.Chrome(chrome_options=options) #Can be changed to Firefox as well
        #driver.get("http://bloodrizer.ru/games/kittens/") #Loads the kittens game
        driver.get("file:///u/gstone/kitten-game/index.html") #Loads the kittens game
        #Wait for deferred loading
        #initGame unhides the #game element
        try:
            WebDriverWait(driver, 20, 0.1).until(
                EC.visibility_of(driver.find_element(By.ID, "game"))) #Tries for 20 seconds to load kittens game
                #We are waiting for the game to open for 20 seconds. Once it opens we will launch Simba
        except TimeoutException: #If the game does not load in 20 seconds
            print("Warning: Unable to start game", file=sys.stderr)
            driver.close() #Close the game
            return 0
        driver.execute_script(botJs) #Loads Simba (bot js)
       # driver.execute_script("importSaveDecompressed(arguments[0]);", simbaSettings) #Give genome information through Simba
        # See https://selenium-python.readthedocs.io/waits.html
        try:
            # When the simulation is finished, the JS will create an element
            # with ID "fitnessValue"
            timeout_seconds = 1000
            WebDriverWait(driver, timeout_seconds, 6).until( #Waiting for element Simba will create when it's done
                    EC.presence_of_element_located((By.ID, "runFinished")))
        except TimeoutException:
            print("Warning: Worker timeout", file=sys.stderr)

        try:
            fitnessElement = WebDriverWait(driver, 1).until( #Get the fitness
                    EC.presence_of_element_located((By.ID, "fitnessValue")))
            result = int(fitnessElement.get_attribute('innerHTML').strip()) #Retrieves fitness score
        except TimeoutException:
            print("Warning: Unable to retrieve fitness value", file=sys.stderr)
            result = 0

        if displayPage:
            print(re.sub(r'\n[\s]*\n', '\n', driver.find_element_by_tag_name('html').text))
        return result
    except (WebDriverException, HTTPError) as ex:
        print("Warning: Selenium run failed:", ex, file=sys.stderr)
        return 0
    finally:
        try:
            if driver:
                driver.close() #Closes everything: Simba and kittens game
        except (WebDriverException, HTTPError):
            print("Warning: Chrome did not close promptly", file=sys.stderr)

def main(argv): #Used for testing. Import file as a module and call run browser
    #defaultSettings = '{"queue": [{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Hut","tab":"Bonfire","panel":""},{"name":"Barn","tab":"Bonfire","panel":""},{"name":"Library","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Hut","tab":"Bonfire","panel":""},{"name":"Barn","tab":"Bonfire","panel":""},{"name":"Library","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Hut","tab":"Bonfire","panel":""},{"name":"Barn","tab":"Bonfire","panel":""},{"name":"Library","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Hut","tab":"Bonfire","panel":""},{"name":"Barn","tab":"Bonfire","panel":""},{"name":"Library","tab":"Bonfire","panel":""},{"name":"Catnip field","tab":"Bonfire","panel":""},{"name":"Hut","tab":"Bonfire","panel":""},{"name":"Barn","tab":"Bonfire","panel":""},{"name":"Library","tab":"Bonfire","panel":""}], "jobQueue": [], "geneticAlgorithm": true, "speed": 8192, "disableTimeskip": true, "desiredTicksPerLoop": 16, "running": true}'
    import genetic
    if (len(argv) >= 2):
        import pickle
        generation = pickle.load(open(argv[1], "rb"))
        genome = generation[0][2]
    else:
        genome = genetic.KittensProblem(genetic.allQueueables, len(genetic.allQueueables) * 3).randomGenome()
    defaultSettings = genetic.toSimbaSettings(genome)
    if (len(argv) < 2):
        print(defaultSettings)
    print(run_browser(defaultSettings, len(argv) <= 1))

if __name__ == '__main__':
    main(sys.argv)
