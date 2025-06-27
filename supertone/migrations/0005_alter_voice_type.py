from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("supertone", "0004_alter_supertoneline_voice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voice",
            name="voice_id",
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
    ]
