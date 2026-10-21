import random

def generate_lyrics(name, message):

    templates = [

f"""
🎵 HAPPY BIRTHDAY {name.upper()} 🎵

Verse 1

Today is the special day for {name}
Everybody is here to celebrate {name}

Friends are smiling
Family is singing too

Because today belongs to {name}

Chorus

Happy Birthday {name}
Happy Birthday {name}

May your dreams come true today

Happy Birthday {name}
Happy Birthday {name}

We're all celebrating you

Special Message

{message}

Happy Birthday {name}
""",

f"""
🎵 CELEBRATION SONG 🎵

Verse 1

Let's all sing for {name}
Let's all cheer for {name}

What a wonderful day it is

Today we celebrate {name}

Chorus

Happy Birthday {name}

Have a wonderful day

Happy Birthday {name}

Let's celebrate your way

Special Message:

{message}

Happy Birthday {name}
Happy Birthday {name}
""",

f"""
🎵 PARTY TIME 🎵

Verse 1

Balloons are flying high

Everybody is saying hi

Because today is all about {name}

Chorus

Happy Birthday {name}
Happy Birthday {name}

May happiness stay with you

Special Message

{message}

From all your friends and family

Happy Birthday {name}
"""

    ]

    return random.choice(templates)
