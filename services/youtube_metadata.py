def get_youtube_metadata(
    name,
    message
):

    title = (
        f"Happy Birthday {name} | Personalized Birthday Song & Wishes"
    )

    description = f"""
Happy Birthday {name} 🎉

{message}

Personalized birthday wishes video.

#happybirthday
#{name.lower()}
#birthdaysong
#birthdaywishes
#kidsbirthday
"""

    tags = [
        "happy birthday",
        f"happy birthday {name}",
        "birthday song",
        "birthday wishes",
        "kids birthday",
        "birthday celebration",
        name
    ]

    return (
        title,
        description,
        tags
    )
