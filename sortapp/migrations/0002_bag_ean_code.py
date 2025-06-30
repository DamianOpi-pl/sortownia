# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sortapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bag',
            name='ean_code',
            field=models.CharField(blank=True, help_text='EAN-13 barcode for the bag', max_length=13, null=True, unique=True),
        ),
    ]