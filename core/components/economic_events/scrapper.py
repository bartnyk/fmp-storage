import logging
import random
from collections import Counter
from datetime import datetime, time

from core.components.economic_events import errors
from core.components.economic_events.models import Country, EventList
from core.config import cfg
from core.scrapper.base import BaseScrapper
from core.scrapper.utils import wait_random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

logger = logging.getLogger("scrapper_logger")

subjects_names = Country.get_subject_names()


class EconomicEventsScrapperV1(BaseScrapper):
    source_url: str = str(cfg.fmp.events_source_url)

    def __init__(self, recent_only: bool = False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._date_from = self._date_to = None
        self._ready = False
        self._fresh_filters = True
        self._recent_only = recent_only

    def prepare(self) -> None:
        """
        Prepare the scrapper by changing filters.

        """
        self._change_timezone()
        self._change_countries()
        self._ready = True

    def setup(self, from_date: datetime.date = None, to_date: datetime.date = None) -> None:
        """
        Get economic events for the given date range.

        Parameters
        ----------
        from_date : datetime.date
            Start date.
        to_date : datetime.date
            End date.

        Returns
        -------
        EventList
            List of economic events.

        """
        if not self._ready:
            self.prepare()

        if not self._recent_only:
            self._change_date_filter(from_date, to_date)

        self._validate_current_filters()

    def _define_sentiment(self, cell: WebElement) -> int:
        """
        Define the sentiment of the event.

        Parameters
        ----------
        cell : WebElement
            Cell element.

        Returns
        -------
        int
            Sentiment value.

        """
        return 1 if "positive" in cell.get_attribute("class") else 0

    def get_data(self) -> list[dict]:
        """
        Get the data from the webpage.

        Returns
        -------
        list[dict]
            List of economic events.

        """
        if not self._ready:
            raise errors.ScrapperNotPreparedException("Scrapper is not prepared yet.")

        events: list[dict] = []
        date_cursor: datetime.date = self._date_from

        table: WebElement = self._driver.find_element(By.XPATH, "//*[@id='calendar']")
        rows: list[WebElement] = table.find_elements(By.XPATH, "//tr")
        header_rows: list[WebElement] = table.find_elements(By.XPATH, "//thead[@class='table-header']")
        data_rows: list[WebElement] = table.find_elements(By.XPATH, ".//tr[@data-url]")

        for row in rows:
            if row in data_rows:
                data_cells: list[WebElement] = row.find_elements(By.TAG_NAME, "td")

                if time_raw := data_cells[0].text:
                    cell_time: datetime.time = datetime.strptime(time_raw, "%I:%M %p").time()
                else:
                    cell_time: datetime.time = time(0, 0)

                try:
                    country = Country(data_cells[3].get_property("title"))
                except ValueError:  # Somehow there's a country that does not interest us
                    continue

                sentiment_cell_info = data_cells[6].get_attribute("class")
                sentiment = 1 if "positive" in sentiment_cell_info else 0

                data = {
                    "timestamp": datetime.combine(date_cursor, cell_time, cfg.timezone),
                    "subject": country.subject,
                    "title": data_cells[4].text,
                    "actual": data_cells[5].text,
                    "previous": data_cells[6].text,
                    "consensus": data_cells[7].text,
                    "forecast": data_cells[8].text,
                    "sentiment": sentiment,
                }
                events.append(data)

            elif row.find_element(By.XPATH, "..") in header_rows:
                thead_date: str = row.find_element(By.TAG_NAME, "th").text  # like 'Friday January 01 2021'
                date_cursor: datetime.date = datetime.strptime(thead_date, "%A %B %d %Y").date()

        return events

    @staticmethod
    def parse_objects(data: list[dict]) -> EventList:
        """
        Parse the data into EventList object.

        Parameters
        ----------
        data : list[dict]
            List of economic events.

        Returns
        -------
        EventList
            List of economic events.

        """
        return EventList.model_validate(data)

    @property
    def current_timezone_filter(self) -> str:
        """
        Get the current timezone filter value.

        Returns
        -------
        str
            Current timezone value.

        """
        return self._driver.find_element(By.ID, "DropDownListTimezone").get_attribute("value")

    @property
    def current_date_filter(self) -> tuple[datetime.date, datetime.date]:
        """
        Get the current date filter values.

        Returns
        -------
        tuple[datetime.date, datetime.date]
            Start and end date values

        """
        start_date_input = self._driver.find_element(By.XPATH, "//input[@id='startDate']")
        end_date_input = self._driver.find_element(By.XPATH, "//input[@id='endDate']")
        return start_date_input.get_attribute("value"), end_date_input.get_attribute("value")

    @property
    def current_subjects_filter(self) -> list[str]:
        """
        Get the current subjects filter values.

        Returns
        -------
        list[str]
            List of subjects (countries).

        """
        self._driver.find_element(
            By.XPATH,
            '//button[@type="button" and @class="btn btn-outline-secondary btn-calendar" and @onclick="toggleMainCountrySelection();"]',
        ).click()
        self._driver.implicitly_wait(0.2)  # wait for the countries to load
        checked_elements = self._driver.find_element(By.ID, "te-c-all").find_elements(
            By.XPATH, "//li[input[@checked='']]"
        )
        checked_countries = [element.text for element in checked_elements]
        self._driver.find_element(
            By.XPATH,
            '//button[@type="button" and @class="btn btn-outline-secondary btn-calendar" and @onclick="toggleMainCountrySelection();"]',
        ).click()
        return checked_countries

    def _validate_current_filters(self) -> None:
        """
        Validate the current filters.

        """
        current_timezone = self.current_timezone_filter
        current_subjects = self.current_subjects_filter

        if not self._recent_only:
            current_dates = self.current_date_filter
            expected_dates = (self._date_from.strftime("%Y-%m-%d"), self._date_to.strftime("%Y-%m-%d"))
            if current_dates != expected_dates:
                raise errors.DifferentDatesException(
                    f"Current date filter is set to {current_dates}, but should be set to {expected_dates}."
                )

        if current_timezone != "0":
            raise errors.DifferentTimezoneException(
                f"Timezone is set to {current_timezone}, but should be set to: 0 (UTC)."
            )

        if Counter(current_subjects) != Counter(subjects_names):
            raise errors.DifferentSubjectException(
                f"Current subjects filter is set to {current_subjects}, but should be set to {subjects_names}."
            )

    @wait_random()
    def _change_timezone(self) -> None:
        """
        Change the timezone to UTC.

        """
        timezone_dropdown = self._driver.find_element(By.ID, "DropDownListTimezone")
        timezone_select = Select(timezone_dropdown)
        timezone_select.select_by_visible_text("UTC")
        logger.info("Timezone changed to UTC.")

    @wait_random()
    def _change_date_filter(self, from_date: datetime.date, to_date: datetime.date) -> None:
        """
        Change the date filter and submit the form.

        Parameters
        ----------
        from_date: datetime.date
            Start date.
        to_date : datetime.date
            End date.

        """
        label = "Recent" if self._fresh_filters else "Custom"
        self._date_from, self._date_to = from_date, to_date
        self._driver.find_element(By.XPATH, f"//span[contains(text(), '{label}')]").click()
        self._driver.implicitly_wait(0.2)  # wait for the form to load
        self._driver.find_element(By.XPATH, "//i[@class='bi bi-pencil']/parent::*").click()

        start_date_input = self._driver.find_element(By.XPATH, "//input[@id='startDate']")
        end_date_input = self._driver.find_element(By.XPATH, "//input[@id='endDate']")

        start_date_input.clear()
        start_date_input.send_keys(from_date.strftime("%Y-%m-%d"))

        end_date_input.clear()
        end_date_input.send_keys(to_date.strftime("%Y-%m-%d"))

        self._driver.find_element(By.XPATH, "//button[@class='btn btn-success' and text()='Submit']").click()
        self._fresh_filters = False

    @wait_random()
    def _change_countries(self) -> None:
        """
        Change the countries filter.

        """
        self._driver.find_element(
            By.XPATH,
            '//button[@type="button" and @class="btn btn-outline-secondary btn-calendar" and @onclick="toggleMainCountrySelection();"]',
        ).click()
        self._driver.implicitly_wait(0.2)
        self._driver.find_element(
            By.XPATH,
            '//a[@class="btn btn-outline-secondary te-c-option" and @onclick="clearSelection();"]',
        ).click()
        self._driver.implicitly_wait(0.2)

        countries_element = self._driver.find_element(By.ID, "te-c-all")

        random.shuffle(subjects_names)
        for name in subjects_names:
            if element := countries_element.find_element(By.XPATH, f"//a[@noref='' and text()='{name}']"):
                if not self._gui:
                    ActionChains(self._driver).move_to_element(element).perform()

                element.click()

        countries_element.find_element(By.XPATH, "//a[@onclick='saveSelectionAndGO();']").click()


DEFAULT_SCRAPPER_CLASS = EconomicEventsScrapperV1
