# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, logging.config, os, pprint, re, sys, time, unittest

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append( project_path )

from ocra_selenium_tests import settings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


logging.config.dictConfig( settings.LOGGING_CONF_DCT )
log = logging.getLogger(__name__)


class FacultyAddArticleViaCitationTest( unittest.TestCase ):
    """ Tests adding article via detail method. """

    def setUp(self):
        """ Initializes and gets us to the add-journal-article page. """
        log.debug( 'starting setUp()' )
        self.driver = None
        driver_type = unicode( os.environ.get('OCRA_TESTS__DRIVER_TYPE') )
        if driver_type == u'firefox':
            self.driver = webdriver.Firefox()
        else:
            self.driver = webdriver.PhantomJS( u'%s' % driver_type )  # will be path to phantomjs
        # try:
        #     if driver_type == u'firefox':
        #         self.driver = webdriver.Firefox()
        #     else:
        #         self.driver = webdriver.PhantomJS( u'%s' % driver_type )  # will be path to phantomjs
        # except Exception as e:
        #     log.error( 'problem creating driver, ```{}```'.format(unicode(repr(e))) )
        log.debug( 'driver created' )
        self.driver.implicitly_wait(30)
        self.USERNAME = unicode( os.environ.get(u'OCRA_TESTS__FACULTY_USERNAME') )
        self.PASSWORD = unicode( os.environ.get(u'OCRA_TESTS__FACULTY_PASSWORD') )
        self.base_url = unicode( os.environ.get(u'OCRA_TESTS__FACULTY_START_URL') )
        self.course_password = unicode( os.environ.get(u'OCRA_TESTS__COURSE_PASSWORD') )
        self.driver.get( self.base_url )
        self.test_article_name = u'Seeking God in the Brain — Efforts to Localize Higher Brain Functions'
        self.journal_title = u'New England Journal of Medicine'
        self.article_date = u'2008'
        #
        # test for Shib
        self.assertTrue( 'sso.brown.edu' in self.driver.current_url )

        # login
        self.driver = self._log_into_shib( self.driver )

        # test we've accessed the main faculty work page
        self.assertTrue( 'reserves/cr/faclogin.php' in self.driver.current_url )

        # click the manage-my-reserves link
        self.driver.find_element_by_name("netid").click()

        # test we're at the 'Course Reserves Faculty Interface: Main Menu'
        self.assertTrue( 'reserves/cr/menu.php' in self.driver.current_url )

        # click the 'Add reserves to a current or upcoming class:' 'GRMN 0750E' link
        # self.driver.find_element_by_link_text("GRMN 0750E: Reading Film: An Introduction to German Cinema").click()
        self.driver.find_element_by_partial_link_text("GRMN 0750E").click()  # Reading Film: An Introduction to German Cinema

        # test we're at the GRMN 0750E class page
        self.assertTrue( 'reserves/cr/class/?classid=5734' in self.driver.current_url )

        # click the 'Class Details' link to ensure there is a class password set
        self.driver.find_element_by_link_text("Class Details").click()

        # confirm we're at the class edit page
        self.assertTrue( 'reserves/cr/class/edit.php' in self.driver.current_url )

        # confirm the class password (this particular flow assumes a password exists)
        password_element = self.driver.find_element_by_css_selector( 'input[name="password"]' )
        self.assertEqual(
            self.course_password,
            password_element.get_attribute("value") )

        # hit the back button
        self.driver.back()

        # confirm we're back on the x page
        self.assertTrue( 'reserves/cr/class/?classid=5734' in self.driver.current_url )

        # test that there's no <table data-restype="article"> element (no 'Online Readings' view showing)
        self.driver.implicitly_wait(2)  # because I'm asserting False, and it'll wait until the timeout
        self.assertEqual(
            False,
            self._is_css_selector_found( selector_text='table[data-restype="article"]' )
            )
        self.driver.implicitly_wait(30)

        # click the 'View' link for 'Online Readings'
        self.driver.find_element_by_xpath("(//a[contains(text(),'View')])[2]").click()

        # test that there is a <table data-restype="article"> element
        self.assertEqual(
            True,
            self._is_css_selector_found( selector_text='table[data-restype="article"]' )
            )

        # get the article html
        article_html = self.driver.find_element_by_css_selector( 'table[data-restype="article"]' ).text

        # test that the article to be added is not listed
        # print u'type(self.test_article_name), %s' % type( self.test_article_name )
        # print u'type(article_html), %s' % type( article_html )
        self.assertEqual(
            True,
            self.test_article_name not in article_html
            )

        # click the 'Add' link for 'Online Readings'
        self.driver.find_element_by_xpath("(//a[contains(text(),'Add')])[2]").click()

        # test that we're on the 'What type of material do you want to add?' page
        self.assertTrue( 'reserves/cr/requestarticle.php' in self.driver.current_url )

        # click the 'Journal Article link'
        self.driver.find_element_by_name("subtask").click()

        # test we're on the 'Enter Journal Article Citation' page
        self.assertEqual(
            True,
            'Enter Journal Article Citation' in self.driver.find_element_by_css_selector( 'div#maincontent > h3' ).text
            )

    ## work

    def test_add_article_via_details(self):
        """ Tests faculty add-article via details method.
            Note: specified data entered does not trigger auto-find, so that's not tested.
            Tests that:
            - form submit button does not work until required fields are filled out.
            - submitted data exists on subsequent course page.
            """
        log.debug( 'starting test_add_article_via_details()' )
        driver = self.driver

        # confirm the 'details search' view is not shown
        details_element = driver.find_element_by_css_selector( 'div#articleDetails' )
        self.assertEqual(
            False,
            details_element.is_displayed() )

        # click option 3: 'Enter article details'
        driver.find_element_by_id("ui-accordion-artcit-header-2").click()

        # confirm the 'details search' view is shown
        time.sleep( 1 )
        details_element = driver.find_element_by_css_selector( 'div#articleDetails' )
        self.assertEqual(
            True,
            details_element.is_displayed() )

        # confirm the button is clickable
        button_element = driver.find_element_by_id("details_submit_button")
        self.assertEqual(
            '',
            button_element.get_attribute( 'class' ) )

        # confirm no button-triggered tooltips
        button_element = driver.find_element_by_id("details_submit_button")
        self.assertEqual(
            None,
            button_element.get_attribute('aria-describedby') )
        # print( 'aria-describedby before, %s' % button_element.get_attribute('aria-describedby') )

        # hover over the submit button
        button_element = driver.find_element_by_id("details_submit_button")
        hover = ActionChains(driver).move_to_element(button_element)
        hover.perform()

        # confirm the button-triggered tooltips
        # button_element = driver.find_element_by_id("details_submit_button")
        self.assertEqual(
            'ui-tooltip-0',
            button_element.get_attribute('aria-describedby') )
        # print( 'aria-describedby after hover, %s' % button_element.get_attribute('aria-describedby') )

        # confirm the button is disabled
        self.assertEqual(
            'disabled',
            button_element.get_attribute( 'class' ) )

        # try to click submit anyway, without filling in required fields
        driver.find_element_by_id( 'details_submit_button' ).click()

        # confirm we're still on the same page
        self.assertTrue( 'reserves/cr/requestarticle.php' in self.driver.current_url )

        # confirm the 'details search' view is still shown
        details_element = driver.find_element_by_css_selector( 'div#articleDetails' )
        self.assertEqual(
            True,
            details_element.is_displayed() )

        # enter title
        driver.find_element_by_name("atitle").clear()
        driver.find_element_by_name("atitle").send_keys( self.test_article_name )

        # enter journal title
        driver.find_element_by_name("title").clear()
        driver.find_element_by_name("title").send_keys( self.journal_title )

        # enter date
        driver.find_element_by_css_selector( 'input[class="req datep inp_date hasDatepicker"]' ).clear()  # can't use `id` because it's dynamic
        driver.find_element_by_css_selector( 'input[class="req datep inp_date hasDatepicker"]' ).send_keys( self.article_date )
        driver.find_element_by_css_selector( 'input[class="req datep inp_date hasDatepicker"]' ).send_keys( Keys.TAB )  # submit button not active until leaving required date field.

        # confirm the button is enabled
        time.sleep( 2 )
        self.assertEqual(
            '',
            button_element.get_attribute( 'class' ) )

        # click submit
        driver.find_element_by_id( 'details_submit_button' ).click()

        # confirm user sees the Copyright info
        self.assertEqual(
            True,
            'Copyright' in self.driver.find_element_by_css_selector( 'div#maincontent > h3' ).text
            )

        # confirm entered title is shown on copyright page
        self.assertEqual(
            True,
            self.test_article_name in self.driver.find_element_by_css_selector( 'div#maincontent > blockquote' ).text
            )

        # click the 'The work is a <b>U.S. Government document</b> not protected by copyright' link
        driver.find_element_by_css_selector( 'button[value="gov doc"]' ).click()

        # confirm we've gotten to the 'Place PDFs on E-Reserves' screen
        self.assertEqual(
            True,
            'Place PDFs on E-Reserves' in self.driver.find_element_by_css_selector( 'div#maincontent > h3' ).text
            )

        # confirm the 'pdf upload' section is visible
        pdf_upload_element = driver.find_element_by_css_selector( 'div#pdfupload' )
        self.assertEqual(
            True,
            pdf_upload_element.is_displayed() )

        # click the 'I will email or upload a PDF at a later time' option
        driver.find_element_by_name("ereserve").click()

        # assert we're back to the course page via url
        self.assertTrue( 'reserves/cr/class/?classid=5734' in self.driver.current_url )

        # confirm the confirmation block exists
        self.assertEqual(
            True,
            'New article' in self.driver.find_element_by_css_selector( 'p[class="notice success"]' ).text
            )

        # click the 'View' link for 'Online Readings'
        driver.find_element_by_xpath("(//a[contains(text(),'View')])[2]").click()

        # get the article html
        article_html = driver.find_element_by_css_selector( 'table[data-restype="article"]' ).text

        # test that the added article is listed
        self.assertEqual(
            True,
            self.test_article_name in article_html
            )

        # determine delete link
        article_table_element = driver.find_element_by_css_selector( 'div#articles > table > tbody' )
        table_rows = article_table_element.find_elements_by_tag_name( 'tr' )
        target_row_counter = 1  # because xpath call is 1-indexed, not zero-indexed
        for row in table_rows:
            if self.test_article_name in row.text:
                break
            else:
                target_row_counter += 1
        # print( '- TARGET ROW COUNTER, %s' % target_row_counter )

        # click the delete link
        driver.find_element_by_xpath( "(//a[contains(text(),'Delete')])[%s]" % target_row_counter ).click()

        # test that the added article is no longer listed
        time.sleep( 2 )  # needed; an immediate check will still show the text of the deleted citation
        article_html = driver.find_element_by_css_selector( 'table[data-restype="article"]' ).text
        self.assertTrue( self.test_article_name not in article_html )

    ## helper functions

    def _is_css_selector_found( self, selector_text ):
        """ Helper function to make assert test-statements cleaner. """
        try:
            self.driver.find_element_by_css_selector( selector_text )
            return True
        except NoSuchElementException as e:
            return False

    def _log_into_shib( self, driver ):
        """ Helper function for tests.
            Takes driver; logs in user; returns driver.
            Called by module test functions. """
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys( self.USERNAME )
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys( self.PASSWORD )
        driver.find_element_by_css_selector("button[type=\"submit\"]").click()
        return driver

    ##

    def tearDown(self):
        self.driver.quit()
        # self.assertEqual([], self.verificationErrors)



if __name__ == "__main__":
    # print u'about to run test'
    runner = unittest.TextTestRunner( verbosity=2 )
    unittest.main( testRunner=runner )  # python2
    # print u'test done'
    # unittest.main( verbosity=2, warnings='ignore' )  # python3; warnings='ignore' from <http://stackoverflow.com/a/21500796>
