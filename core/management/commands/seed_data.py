import random
from django.core.management.base import BaseCommand
from core.models import User, Project, Course, Contest
from django.utils import timezone

class Command(BaseCommand):
    help = 'Saytni demo ma\'lumotlar bilan to\'ldirish'

    def handle(self, *args, **kwargs):
        self.stdout.write('Demo ma\'lumotlar yaratilmoqda...')
        
        # 1. Userlarni tekshirish yoki yaratish
        user, created = User.objects.get_or_create(
            phone='+998901234567',
            defaults={
                'first_name': 'Iqtidorli',
                'last_name': 'Yosh',
                'role': 'yosh',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'Admin user yaratildi: {user.phone}')

        # 2. Kurslar
        courses_data = [
            ('Sun\'iy intellekt asoslari', 'Python va AI dunyosiga birinchi qadam'),
            ('Startapni qanday boshlash kerak?', 'G\'oyadan birinchi milliongacha bo\'lgan yo\'l'),
            ('Zamonaviy Web Dizayn', 'Figma va UI/UX qoidalari'),
        ]
        for title, desc in courses_data:
            c, created = Course.objects.get_or_create(title=title, defaults={'description': desc, 'author': user})
            if created: self.stdout.write(f'Kurs yaratildi: {title}')

        # 3. Startaplar va Loyihalar
        startups_data = [
            {
                'title': 'GreenEnergy.uz',
                'description': 'Quyosh panellarini smart boshqarish tizimi. Biz ekologik toza energiya sarfini optimallashtiramiz.',
                'is_startup': True,
                'funding_goal': 50000000,
                'funding_collected': 12000000,
                'status': 'funding',
                'needs_team': True,
                'required_resources': 'PHP va Python dasturchilar, marketing mutaxassisi'
            },
            {
                'title': 'SmartEdu Platform',
                'description': 'Maktab o\'quvchilari uchun AI orqali shaxsiy repetitor. Har bir bolaning bilim darajasini tahlil qiladi.',
                'is_startup': True,
                'funding_goal': 100000000,
                'funding_collected': 85000000,
                'status': 'dev',
                'needs_team': False,
            },
            {
                'title': 'EcoDeliver',
                'description': 'Elektr samokatlarda tezkor va arzon yetkazib berish xizmati. Biz shahar havosini toza saqlaymiz.',
                'is_startup': True,
                'funding_goal': 25000000,
                'funding_collected': 30000000,
                'status': 'profit',
                'needs_team': True,
                'required_resources': 'Kuryerlar, ofis jihozlari'
            },
            {
                'title': 'RoboLab Yoshlar Markazi',
                'description': 'Robototexnika va muhandislikni o\'rgatuvchi zamonaviy markaz. Bolalarni kelajak kasblariga tayyorlaymiz.',
                'is_startup': False,
                'status': 'active',
            }
        ]
        
        for s in startups_data:
            p, created = Project.objects.get_or_create(title=s['title'], defaults={
                'user': user,
                'description': s['description'],
                'is_startup': s.get('is_startup', False),
                'funding_goal': s.get('funding_goal', 0),
                'funding_collected': s.get('funding_collected', 0),
                'status': s.get('status', 'idea'),
                'needs_team': s.get('needs_team', False),
                'required_resources': s.get('required_resources', ''),
            })
            if created: self.stdout.write(f'Loyiha yaratildi: {s["title"]}')

        self.stdout.write(self.style.SUCCESS('Muaffaqiyatli yakunlandi!'))
