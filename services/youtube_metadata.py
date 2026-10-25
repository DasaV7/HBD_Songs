def get_metadata(
    name,
    message
):

    title = (
        f"Happy Birthday {name} 🎂 | Personalized Birthday Wishes Song"
    )

    description = f"""
Happy Birthday {name}!

{message}

Celebrate a special birthday with beautiful wishes and music.

🎂 Personalized Birthday Video
🎉 Birthday Celebration
🎈 Birthday Music

#HappyBirthday
#{name}
#BirthdaySong
#BirthdayWishes
#KidsBirthday
#BirthdayCelebration
"""

    tags = [

        "happy birthday",

        f"happy birthday {name}",

        "birthday wishes",

        "birthday song",

        "kids birthday",

        "birthday celebration",

        name
    ]

    return (
        title,
        description,
        tags
    )
