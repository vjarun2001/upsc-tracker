from django.db import migrations

QUOTES = [
    ("Success is the sum of small efforts repeated day in and day out.", "Robert Collier"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Well begun is half done.", "Aristotle"),
    ("Do not wait for the perfect moment, take the moment and make it perfect.", ""),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("Consistency is what transforms average into excellence.", ""),
    ("The exam doesn't test what you know. It tests who you've become.", ""),
    ("Small daily improvements are the key to staggering long-term results.", ""),
    ("Every hour of focused study today is an hour closer to the LBSNAA.", ""),
    ("Hard days build the officer you are becoming.", ""),
    ("Revision is where marks are actually won.", ""),
    ("Your only competition is who you were yesterday.", ""),
    ("Focus on being productive instead of busy.", "Tim Ferriss"),
    ("The pain of discipline is far less than the pain of regret.", ""),
    ("One more revision. One more mock test. One more day of discipline.", ""),
]


def seed_quotes(apps, schema_editor):
    Quote = apps.get_model("core", "Quote")

    for text, author in QUOTES:
        Quote.objects.get_or_create(text=text, defaults={"author": author})


def remove_quotes(apps, schema_editor):
    Quote = apps.get_model("core", "Quote")
    Quote.objects.filter(text__in=[text for text, _ in QUOTES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_quotes, remove_quotes),
    ]
