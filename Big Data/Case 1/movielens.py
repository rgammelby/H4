from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Starts a Spark session named "MovieLens"
spark = SparkSession.builder.appName("MovieLens").getOrCreate()

# Reads working dataset
movies_df = spark.read.csv("movies.csv", header=True, inferSchema=True)
ratings_df = spark.read.csv("ratings.csv", header=True, inferSchema=True)
tags_df = spark.read.csv("tags.csv", header=True, inferSchema=True)
links_df = spark.read.csv("links.csv", header=True, inferSchema=True)

# Joins .csv files into a cohesive dataset (full_df)
full_df = (
    ratings_df
    .join(movies_df, on="movieId", how="inner")  # keep only movies with ratings
    .join(tags_df, on=["movieId", "userId"], how="left")  # optional tags
    .join(links_df, on="movieId", how="left")  # optional links
    .cache()  # store in memory for swift repeated queries
)

# Orders columns of cohesive dataset
full_df = full_df.select(
    "userId",
    "movieId",
    "title",
    "genres",
    "rating",
    "timestamp",
    "tag",
    "imdbId",
    "tmdbId"
)

# Inspect the first rows to confirm the weave
full_df.show(5, truncate=False)
