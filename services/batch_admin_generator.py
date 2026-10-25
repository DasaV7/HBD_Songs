import pandas as pd

df = pd.read_csv(
    "data/kids_birthdays.csv"
)

for _, row in df.iterrows():

    name = row["name"]

    message = row["message"]

    print(
        f"Generating {name}"
    )

    # create video

    # upload youtube

    # save youtube link
