# Generated manually for testing cleanup

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge_20250830_1849'),
    ]

    operations = [
        # Clean up any remaining problematic data
        migrations.RunSQL(
            # Forward SQL - clean up any remaining problematic data
            """
            -- Delete any remaining AlertaUsuario records if they exist
            DELETE FROM core_alertausuario WHERE 1=1;
            
            -- Delete any remaining Alerta records if they exist  
            DELETE FROM core_alerta WHERE 1=1;
            
            -- Delete any remaining ProductoTienda records if they exist
            DELETE FROM core_productotienda WHERE 1=1;
            
            -- Clean up any other problematic tables
            DELETE FROM core_newalertausuario WHERE 1=1;
            """,
            # Reverse SQL - no reverse operation needed
            """
            -- No reverse operation
            """
        ),
    ]


