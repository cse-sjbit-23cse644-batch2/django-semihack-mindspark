from django.db import models

class Syllabus(models.Model):

    SUBJECT_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('project', 'Project'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Faculty Review'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]

    subject_name = models.CharField(max_length=200)
    subject_code = models.CharField(max_length=50)

    subject_type = models.CharField(
        max_length=20,
        choices=SUBJECT_TYPE_CHOICES
    )

    l_hours = models.IntegerField(default=0)
    t_hours = models.IntegerField(default=0)
    p_hours = models.IntegerField(default=0)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject_name


class Module(models.Model):
    syllabus = models.ForeignKey(
        Syllabus,
        related_name='modules',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title