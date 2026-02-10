from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('buyerprices', '0002_buyerprice_remove_rubberprice_buyer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='buyerprice',
            name='effective_from',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),
        migrations.AddField(
            model_name='buyerprice',
            name='effective_to',
            field=models.DateTimeField(default=lambda: django.utils.timezone.now() + django.utils.timezone.timedelta(days=1), db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='buyerprice',
            index_together={('buyer', 'effective_from', 'is_active'), ('grade', 'effective_from')},
        ),
        migrations.AlterUniqueTogether(
            name='buyerprice',
            unique_together={('buyer', 'grade', 'custom_grade_name', 'effective_from', 'is_active')},
        ),
        migrations.RemoveField(
            model_name='buyerprice',
            name='effective_date',
        ),
    ]
