from decimal import Decimal
from django.conf import settings
from django.db import models
from django.urls import reverse
from accounts.models import Student
from core.models import Semester
from course.models import Course

# Modified grade constants
A = "A"
B = "B"
C = "C"
D = "D"
SUPP = "Supp"  # Supplementary

GRADE_CHOICES = (
    (A, "A"),
    (B, "B"),
    (C, "C"),
    (D, "D"),
    (SUPP, "Supp"),
)

PASS = "PASS"
FAIL = "FAIL"

COMMENT_CHOICES = (
    (PASS, "PASS"),
    (FAIL, "FAIL"),
)

# Modified grade boundaries
GRADE_BOUNDARIES = [
    (70, A),    # Above 70%
    (60, B),    # 61-70%
    (50, C),    # 51-60%
    (40, D),    # 40-50%
    (0, SUPP),  # Below 40% - Supplementary
]

# Modified grade point mapping
GRADE_POINT_MAPPING = {
    A: 4.0,
    B: 3.0,
    C: 2.0,
    D: 1.0,
    SUPP: 0.0,
}

class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="taken_courses"
    )
    assignment = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    mid_exam = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    quiz = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    attendance = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    final_exam = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    grade = models.CharField(
        choices=GRADE_CHOICES, max_length=4, blank=True, editable=False
    )
    point = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    comment = models.CharField(
        choices=COMMENT_CHOICES, max_length=200, blank=True, editable=False
    )

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.course.slug})

    def __str__(self):
        return f"{self.course.title} ({self.course.code})"

    def get_total(self):
        return sum(
            [
                Decimal(self.assignment),
                Decimal(self.mid_exam),
                Decimal(self.quiz),
                Decimal(self.attendance),
                Decimal(self.final_exam),
            ]
        )

    def get_grade(self):
        total = self.total
        for boundary, grade in GRADE_BOUNDARIES:
            if total >= boundary:
                return grade
        return SUPP

    def get_comment(self):
        if self.grade == SUPP:
            return FAIL
        return PASS

    def get_point(self):
        credit = self.course.credit
        grade_point = GRADE_POINT_MAPPING.get(self.grade, 0.0)
        return Decimal(credit) * Decimal(grade_point)

    def save(self, *args, **kwargs):
        self.total = self.get_total()
        self.grade = self.get_grade()
        self.point = self.get_point()
        self.comment = self.get_comment()
        super().save(*args, **kwargs)

    def calculate_gpa(self):
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return Decimal("0.00")

        taken_courses = TakenCourse.objects.filter(
            student=self.student,
            course__level=self.student.level,
            course__semester=current_semester.semester,
        )

        total_points = sum(tc.point for tc in taken_courses)
        total_credits = sum(tc.course.credit for tc in taken_courses)

        if total_credits > 0:
            gpa = total_points / Decimal(total_credits)
            return round(gpa, 2)
        return Decimal("0.00")

    def calculate_cgpa(self):
        taken_courses = TakenCourse.objects.filter(student=self.student)

        total_points = sum(tc.point for tc in taken_courses)
        total_credits = sum(tc.course.credit for tc in taken_courses)

        if total_credits > 0:
            cgpa = total_points / Decimal(total_credits)
            return round(cgpa, 2)
        return Decimal("0.00")


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    gpa = models.FloatField(null=True)
    cgpa = models.FloatField(null=True)
    semester = models.CharField(max_length=100, choices=settings.SEMESTER_CHOICES)
    session = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=25, choices=settings.LEVEL_CHOICES, null=True)

    def __str__(self):
        return f"Result for {self.student} - Semester: {self.semester}, Level: {self.level}"