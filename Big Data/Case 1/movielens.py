from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, split, explode, from_unixtime, year
import pandas as pd
import matplotlib.pyplot as plt

# Set up Spark session
spark = SparkSession.builder.appName("MovieLensAnalysis").getOrCreate()

# Reads dataset (csv) into memory
movies_df = spark.read.csv("input/movies.csv", header=True, inferSchema=True)
ratings_df = spark.read.csv("input/ratings.csv", header=True, inferSchema=True)
tags_df = spark.read.csv("input/tags.csv", header=True, inferSchema=True)
links_df = spark.read.csv("input/links.csv", header=True, inferSchema=True)

# Rename one of the timestamp columns; was causing a conflict
tags_df = tags_df.withColumnRenamed("timestamp", "tag_timestamp")

# Joins all .csv files into a cohesive dataset and cache
full_df = (
    ratings_df
    .join(movies_df, on="movieId", how="inner")
    .join(tags_df, on=["movieId", "userId"], how="left")
    .join(links_df, on="movieId", how="left")
    .cache()
)

# Convert timestamps from unix time into a human readable format
full_df = (
    full_df
    .withColumn("rating_timestamp_hr", from_unixtime(col("timestamp")))
    .withColumn("tag_timestamp_hr", from_unixtime(col("tag_timestamp")))
)

# Determine the count of unique movies in the dataset
unique_counts = {
    "unique_movies": full_df.select("movieId").distinct().count(),
    "unique_users": full_df.select("userId").distinct().count(),
}

# Write count of unique movies to .csv
pd.DataFrame([unique_counts]).to_csv("output/unique_counts.csv", index=False)

# Determine the average rating for each movie in the dataset 
avg_ratings = (
    full_df
    .groupBy("movieId", "title")
    .agg(avg("rating").alias("avg_rating"))
)
# Data frame was coalesced in an attempt to write to .csv sans metadata, but this did not work. Excuse the funky format. Ditto for every following coalescence.
avg_ratings.coalesce(1).write.csv("output/avg_ratings_per_movie.csv", header=True, mode="overwrite")

# Isolate 10 movies with the highest possible rating (5)
top10_movies = (
    avg_ratings
    .orderBy(col("avg_rating").desc())
    .limit(10)
)
top10_movies.coalesce(1).write.csv("output/top10_movies.csv", header=True, mode="overwrite")

# Determine and display the ratings of a single movie (in this case Toy Story) for each year over a period of 10 years
film_title = "Toy Story (1995)"
film_ratings = (
    full_df
    .filter(col("title") == film_title)
    .withColumn("year", year(col("rating_timestamp_hr")))
)

# Determine the latest year present in the dataset
latest_year = film_ratings.agg({"year": "max"}).collect()[0][0]

# and start with 10 years before that
ten_years_ago = latest_year - 10

film_ratings_10yr = (
    film_ratings
    .filter((col("year") >= ten_years_ago) & (col("year") <= latest_year))
)

film_ratings_summary = (
    film_ratings_10yr
    .groupBy("year")
    .agg(avg("rating").alias("avg_rating"))
    .orderBy("year")
)
film_ratings_summary.coalesce(1).write.csv(f"output/{film_title.replace(' ', '_')}_ratings_10yr.csv", header=True, mode="overwrite")

# Convert data frame to Pandas for chart plotting
fig_film_ratings_10yr = film_ratings_summary.toPandas()

# Plot using matplotlib
plt.figure(figsize=(10,6))
plt.plot(
    fig_film_ratings_10yr['year'], 
    fig_film_ratings_10yr['avg_rating'], 
    marker='o', 
    linestyle='-',
    color='teal'
)
plt.title(f"Average Movie Rating of {film_title} Over 10 Years")
plt.xlabel("Year")
plt.ylabel("Average Rating")
plt.grid(True, linestyle='--', alpha=0.5)
plt.xticks(fig_film_ratings_10yr['year'], rotation=45)
plt.tight_layout()
plt.savefig("output/film_ratings_10yr.png")
plt.close()


# Determine the average user rating for each genre
# Explode genres to isolate each unique genre
genres_df = full_df.withColumn("genre", explode(split(col("genres"), "\\|")))

genre_avg_ratings = (
    genres_df
    .groupBy("genre")
    .agg(avg("rating").alias("avg_rating"))
    .orderBy("avg_rating", ascending=False)
)
genre_avg_ratings.coalesce(1).write.csv("output/genre_avg_ratings.csv", header=True, mode="overwrite")

genre_avg_ratings = (
    genres_df
    .groupBy("genre")
    .agg(avg("rating").alias("avg_rating"))
    .orderBy("avg_rating", ascending=False)
)

# Convert to Pandas
genre_avg_pd = genre_avg_ratings.toPandas()

# Plot bar chart
plt.figure(figsize=(12,6))
plt.bar(genre_avg_pd['genre'], genre_avg_pd['avg_rating'], color='coral')
plt.title("Average Rating by Genre")
plt.xlabel("Genre")
plt.ylabel("Average Rating")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/genre_avg_rating.png")
plt.close()

