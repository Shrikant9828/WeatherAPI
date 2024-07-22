import os
import logging
from datetime import datetime
from django.db.models import Q
from django.db import transaction
from django.db.models import Avg, Sum
from .models import WeatherRecord, Statistic
from django.db.models.functions import ExtractYear

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="log.log",
)
logger = logging.getLogger(__name__)


def read_data():
    """Reads weather data from txt files in the 'data/wx_data' folder and returns a list of WeatherRecord objects."""
    logger.info("Reading txt files to dump data")
    folder = "data/wx_data"
    weather_data = []
    try:
        with transaction.atomic():
            for file in os.scandir(folder):
                if file.name.endswith(".txt"):
                    station = file.name.split(".")[0]

                    with open(file.path, "r") as input_file:
                        for row in input_file:
                            data = row.strip().split("\t")
                            try:
                                date = (
                                    datetime.strptime(data[0], "%Y%m%d").date()
                                    if data[0] != "-9999"
                                    else None
                                )
                                maximum_temperature = (
                                    int(data[1]) if data[1] != "-9999" else None
                                )
                                minimum_temperature = (
                                    int(data[2]) if data[2] != "-9999" else None
                                )
                                precipitation = (
                                    int(data[3]) if data[3] != "-9999" else None
                                )
                            except (ValueError, IndexError):
                                logging.warning(f"Skipping invalid data row: {row}")
                                continue

                            weather_data.append(
                                WeatherRecord(
                                    station=station,
                                    date=date,
                                    maximum_temperature=maximum_temperature,
                                    minimum_temperature=minimum_temperature,
                                    precipitation=precipitation,
                                )
                            )

        end = datetime.now()
        logging.info(f"File reading completed found {len(weather_data)} rows")
        return weather_data
    except Exception as e:
        logging.error(f"Error during ingestion: {str(e)}")


def dump_wx_data():
    """Reads weather data using read_data() and bulk inserts it into the WeatherRecord model."""
    start = datetime.now()
    weather_data = []
    try:
        weather_data = read_data()
        WeatherRecord.objects.bulk_create(weather_data, ignore_conflicts=True)
    except Exception as e:
        logger.error(f"Error in inserting weather row: {e}")
    finally:
        end = datetime.now()
        logger.info(
            f"Weather Data inserted in : {(end-start).total_seconds()} seconds. Rows count: {len(weather_data)}"
        )


def dump_statistics():
    """Calculates and bulk inserts yearly statistics for each weather station into the Statistic model."""
    start = datetime.now()
    statistics_list = []
    try:
        statistics = (
            WeatherRecord.objects.exclude(
                Q(maximum_temperature=None)
                | Q(minimum_temperature=None)
                | Q(precipitation=None)
            )
            .annotate(year=ExtractYear("date"))
            .values("station", "year")
            .annotate(
                average_max_temperature=Avg("maximum_temperature"),
                average_min_temperature=Avg("minimum_temperature"),
                total_precipitation=Sum("precipitation"),
            )
        )
        statistics_list = [
            Statistic(
                station=stat["station"],
                year=stat["year"],
                average_max_temperature=stat["average_max_temperature"],
                average_min_temperature=stat["average_min_temperature"],
                total_precipitation=stat["total_precipitation"],
            )
            for stat in statistics
        ]
        Statistic.objects.bulk_create(statistics_list, ignore_conflicts=True)
    except Exception as e:
        logger.error(f"Error in inserting statistics row: {e}")
    finally:
        end = datetime.now()
        logger.info(
            f"Statistics Data inserted in : {(end-start).total_seconds()} seconds. Rows count: {len(statistics_list)}"
        )
