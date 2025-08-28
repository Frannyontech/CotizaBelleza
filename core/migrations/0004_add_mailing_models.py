# Generated manually for mailing system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_alertausuario_alerta_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('subject', models.CharField(max_length=200)),
                ('html_content', models.TextField()),
                ('text_content', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Plantilla de Email',
                'verbose_name_plural': 'Plantillas de Email',
            },
        ),
        migrations.CreateModel(
            name='MailLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_email', models.EmailField(max_length=254)),
                ('precio_actual', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_objetivo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tienda_url', models.URLField(blank=True, max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('sent', 'Enviado'), ('failed', 'Fallido'), ('cancelled', 'Cancelado')], default='pending', max_length=20)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('error_message', models.TextField(blank=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('alerta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mail_logs', to='core.alertaprecioproductopersistente')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mail_logs', to='core.productopersistente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mail_logs', to='auth.user')),
            ],
            options={
                'verbose_name': 'Log de Email',
                'verbose_name_plural': 'Logs de Email',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.AddField(
            model_name='alertaprecioproductopersistente',
            name='notificada',
            field=models.BooleanField(default=False),
        ),
    ]
