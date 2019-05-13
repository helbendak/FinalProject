from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EndToEndTestCase(LiveServerTestCase):
    def setUp(self):
        self.selenium = webdriver.Safari()
        super(EndToEndTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(EndToEndTestCase, self).tearDown()

    def test_empty_database(self):
        selenium = self.selenium
        selenium.get('http://127.0.0.1:8000/search/')
        # Input Data
        gse_id = selenium.find_element_by_id("gse_input")
        expression_values_document = selenium.find_element_by_id("log_expression_values")
        gene_format_input = selenium.find_element_by_id("gene_format_input")
        submit = selenium.find_element_by_id("submit")
        gse_id.send_keys('GSE85499')
        path = os.path.join(BASE_DIR, "finalProject/test_helpers/gse85499_log_expression.csv")
        expression_values_document.send_keys(path)
        gene_format_input.send_keys("names")
        submit.click()
        # Match attribute names
        WebDriverWait(selenium, 400).until(EC.presence_of_element_located((By.ID, 'existing_features_match')))
        submit = selenium.find_element_by_id("submit")
        submit.click()
        # Match attribute values
        WebDriverWait(selenium, 400).until(EC.presence_of_element_located((By.ID, 'existing_terms')))
        submit = selenium.find_element_by_id("submit")
        submit.click()
        # Show PCA
        WebDriverWait(selenium, 400).until(EC.presence_of_element_located((By.ID, 'show')))
        show = selenium.find_element_by_id("show")
        show.click()
        # Choose split
        WebDriverWait(selenium, 400).until(EC.presence_of_element_located((By.ID, 'show')))
        threshold = selenium.find_element_by_id('threshold')
        threshold.send_keys(0)
        submit = selenium.find_element_by_id("submit")
        submit.click()
        # Test model
        supervised_submit = selenium.find_element_by_id("supervised_submit")
        supervised_submit.click()
        WebDriverWait(selenium, 400).until(EC.presence_of_element_located((By.ID, 'pca_test')))
        selenium.close()
