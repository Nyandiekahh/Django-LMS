from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

# from reportlab.platypus.tables import Table
from reportlab.lib.units import inch
from reportlab.lib import colors

from core.models import Session, Semester
from course.models import Course
from accounts.models import Student
from accounts.decorators import lecturer_required, student_required
from .models import TakenCourse, Result


CM = 2.54


# ########################################################
# Score Add & Add for
# ########################################################
@login_required
@lecturer_required
def add_score(request):
    """
    Shows a page where a lecturer will select a course allocated
    to him for score entry. in a specific semester and session
    """
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    if not current_session or not current_semester:
        messages.error(request, "No active semester found.")
        return render(request, "result/add_score.html")

    # semester = Course.objects.filter(
    # allocated_course__lecturer__pk=request.user.id,
    # semester=current_semester)
    courses = Course.objects.filter(
        allocated_course__lecturer__pk=request.user.id
    ).filter(semester=current_semester)
    context = {
        "current_session": current_session,
        "current_semester": current_semester,
        "courses": courses,
    }
    return render(request, "result/add_score.html", context)


@login_required
@lecturer_required
def add_score_for(request, id):
    """
    Shows a page where a lecturer will add score for students that
    are taking courses allocated to him in a specific semester and session
    """
    current_session = Session.objects.get(is_current_session=True)
    current_semester = get_object_or_404(
        Semester, is_current_semester=True, session=current_session
    )
    if request.method == "GET":
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id
        ).filter(semester=current_semester)
        course = Course.objects.get(pk=id)
        # myclass = Class.objects.get(lecturer__pk=request.user.id)
        # myclass = get_object_or_404(Class, lecturer__pk=request.user.id)

        # students = TakenCourse.objects.filter(
        # course__allocated_course__lecturer__pk=request.user.id).filter(
        #  course__id=id).filter(
        #  student__allocated_student__lecturer__pk=request.user.id).filter(
        #  course__semester=current_semester)
        students = (
            TakenCourse.objects.filter(
                course__allocated_course__lecturer__pk=request.user.id
            )
            .filter(course__id=id)
            .filter(course__semester=current_semester)
        )
        context = {
            "title": "Submit Score",
            "courses": courses,
            "course": course,
            # "myclass": myclass,
            "students": students,
            "current_session": current_session,
            "current_semester": current_semester,
        }
        return render(request, "result/add_score_for.html", context)

    if request.method == "POST":
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (
                str(key),
            )  # gather all the all students id (i.e the keys) in a tuple
        for s in range(
            0, len(ids)
        ):  # iterate over the list of student ids gathered above
            student = TakenCourse.objects.get(id=ids[s])
            # print(student)
            # print(student.student)
            # print(student.student.program.id)
            courses = (
                Course.objects.filter(level=student.student.level)
                .filter(program__pk=student.student.program.id)
                .filter(semester=current_semester)
            )  # all courses of a specific level in current semester
            total_credit_in_semester = 0
            for i in courses:
                if i == courses.count():
                    break
                total_credit_in_semester += int(i.credit)
            score = data.getlist(
                ids[s]
            )  # get list of score for current student in the loop
            assignment = score[
                0
            ]  # subscript the list to get the fisrt value > ca score
            mid_exam = score[1]  # do the same for exam score
            quiz = score[2]
            attendance = score[3]
            final_exam = score[4]
            obj = TakenCourse.objects.get(pk=ids[s])  # get the current student data
            obj.assignment = assignment  # set current student assignment score
            obj.mid_exam = mid_exam  # set current student mid_exam score
            obj.quiz = quiz  # set current student quiz score
            obj.attendance = attendance  # set current student attendance score
            obj.final_exam = final_exam  # set current student final_exam score

            obj.total = obj.get_total()
            obj.grade = obj.get_grade()

            # obj.total = obj.get_total(assignment, mid_exam, quiz, attendance, final_exam)
            # obj.grade = obj.get_grade(assignment, mid_exam, quiz, attendance, final_exam)

            obj.point = obj.get_point()
            obj.comment = obj.get_comment()
            # obj.carry_over(obj.grade)
            # obj.is_repeating()
            obj.save()
            gpa = obj.calculate_gpa()
            cgpa = obj.calculate_cgpa()

            try:
                a = Result.objects.get(
                    student=student.student,
                    semester=current_semester,
                    session=current_session,
                    level=student.student.level,
                )
                a.gpa = gpa
                a.cgpa = cgpa
                a.save()
            except:
                Result.objects.get_or_create(
                    student=student.student,
                    gpa=gpa,
                    semester=current_semester,
                    session=current_session,
                    level=student.student.level,
                )

            # try:
            #     a = Result.objects.get(student=student.student,
            # semester=current_semester, level=student.student.level)
            #     a.gpa = gpa
            #     a.cgpa = cgpa
            #     a.save()
            # except:
            #     Result.objects.get_or_create(student=student.student, gpa=gpa,
            # semester=current_semester, level=student.student.level)

        messages.success(request, "Successfully Recorded! ")
        return HttpResponseRedirect(reverse_lazy("add_score_for", kwargs={"id": id}))
    return HttpResponseRedirect(reverse_lazy("add_score_for", kwargs={"id": id}))


# ########################################################


@login_required
@student_required
def grade_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(student__student__pk=request.user.id).filter(
        course__level=student.level
    )
    # total_credit_in_semester = 0
    results = Result.objects.filter(student__student__pk=request.user.id)

    result_set = set()

    for result in results:
        result_set.add(result.session)

    sorted_result = sorted(result_set)

    total_first_semester_credit = 0
    total_sec_semester_credit = 0
    for i in courses:
        if i.course.semester == "First":
            total_first_semester_credit += int(i.course.credit)
        if i.course.semester == "Second":
            total_sec_semester_credit += int(i.course.credit)

    previousCGPA = 0
    # previousLEVEL = 0
    # calculate_cgpa
    for i in results:
        previousLEVEL = i.level
        try:
            a = Result.objects.get(
                student__student__pk=request.user.id,
                level=previousLEVEL,
                semester="Second",
            )
            previousCGPA = a.cgpa
            break
        except:
            previousCGPA = 0

    context = {
        "courses": courses,
        "results": results,
        "sorted_result": sorted_result,
        "student": student,
        "total_first_semester_credit": total_first_semester_credit,
        "total_sec_semester_credit": total_sec_semester_credit,
        "total_first_and_second_semester_credit": total_first_semester_credit
        + total_sec_semester_credit,
        "previousCGPA": previousCGPA,
    }

    return render(request, "result/grade_results.html", context)


@login_required
@student_required
def assessment_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(
        student__student__pk=request.user.id, course__level=student.level
    )
    result = Result.objects.filter(student__student__pk=request.user.id)

    context = {
        "courses": courses,
        "result": result,
        "student": student,
    }

    return render(request, "result/assessment_results.html", context)


@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_semester = Semester.objects.get(is_current_semester=True)
    current_session = Session.objects.get(is_current_session=True)
    result = TakenCourse.objects.filter(course__pk=id)
    course = get_object_or_404(Course, id=id)
    no_of_pass = TakenCourse.objects.filter(course__pk=id, comment="PASS").count()
    no_of_fail = TakenCourse.objects.filter(course__pk=id, comment="FAIL").count()
    fname = (
        str(current_semester) + "_semester_" + str(current_session) + "_"
        + str(course) + "_resultSheet.pdf"
    )
    fname = fname.replace("/", "-")
    flocation = settings.MEDIA_ROOT + "/result_sheet/" + fname

    # Create the PDF document with adjusted margins
    doc = SimpleDocTemplate(
        flocation,
        rightMargin=1.5 * CM,
        leftMargin=1.5 * CM,
        topMargin=2 * CM,
        bottomMargin=2 * CM
    )
    
    # Set up styles
    styles = getSampleStyleSheet()
    
    # Add logo style for "Learnify"
    styles.add(ParagraphStyle(
        name='Logo',
        fontSize=40,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e88e5'),  # Material Blue
        spaceAfter=30
    ))
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='SubTitle',
        fontSize=12,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.white
    ))
    
    Story = []

    # Add Learnify Logo Text
    Story.append(Paragraph("Learnify", styles['Logo']))
    Story.append(Spacer(1, 0.2 * inch))

    # Add headers with new styles
    title = f"{str(current_semester)} SEMESTER {str(current_session)} RESULT SHEET"
    Story.append(Paragraph(title, styles['CustomTitle']))
    
    course_info = (
        f"<b>Course:</b> {course.title} ({course.code})<br/>"
        f"<b>Course Lecturer:</b> {request.user.get_full_name}<br/>"
        f"<b>Level:</b> {result.filter(course_id=id).first().course.level}"
    )
    Story.append(Paragraph(course_info, styles['SubTitle']))
    Story.append(Spacer(1, 0.5 * inch))

    # Create header with improved styling
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e88e5')),  # Matching blue for header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
    ])

    # Define column widths for better spacing
    col_widths = [0.7*inch, 1.2*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch]
    
    # Create the header row
    header = [["S/N", "ID NO.", "FULL NAME", "TOTAL", "GRADE", "POINT", "COMMENT"]]
    
    # Add data rows
    data = header + [
        [
            count + 1,
            student.student.student.username.upper(),
            student.student.student.get_full_name.capitalize(),
            student.total,
            student.grade,
            student.point,
            student.comment
        ] for count, student in enumerate(result)
    ]

    # Create the table with the complete data
    table = Table(data, colWidths=col_widths)
    table.setStyle(table_style)
    
    # Add row colors for better readability
    for i in range(1, len(data)):
        if i % 2 == 0:
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f6fa'))
            ]))
        # Highlight failed grades in red
        if data[i][4] == "F" or data[i][4] == "Supp":
            table.setStyle(TableStyle([
                ('TEXTCOLOR', (4, i), (4, i), colors.red)
            ]))

    Story.append(table)
    Story.append(Spacer(1, 1 * inch))

    # Add summary section with improved styling
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    summary_data = [
        [
            Paragraph(f"<b>Date:</b> {'_'*30}", summary_style),
            Paragraph(f"<b>Total Students:</b> {len(result)}", summary_style)
        ],
        [
            Paragraph(f"<b>Signature / Stamp:</b> {'_'*30}", summary_style),
            Paragraph(f"<b>PASS:</b> {no_of_pass} &nbsp;&nbsp;&nbsp; <b>FAIL:</b> {no_of_fail}", summary_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[4*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    Story.append(summary_table)
    
    # Add disclaimer in italics
    Story.append(Spacer(1, 0.5 * inch))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Oblique',  # This makes it italic
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666')
    )
    disclaimer = "This report card was issued without any erasure or alterations whatsoever."
    Story.append(Paragraph('<i>' + disclaimer + '</i>', disclaimer_style))

    # Build the PDF
    doc.build(Story)

    # Return the response
    fs = FileSystemStorage(settings.MEDIA_ROOT + "/result_sheet")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename=' + fname + ''
        return response
    return response

@login_required
@student_required
def course_registration_form(request):
    current_session = Session.objects.get(is_current_session=True)
    courses = TakenCourse.objects.filter(student__student__id=request.user.id)
    fname = request.user.username + ".pdf"
    fname = fname.replace("/", "-")
    # flocation = '/tmp/' + fname
    # print(MEDIA_ROOT + "\\" + fname)
    flocation = settings.MEDIA_ROOT + "/registration_form/" + fname
    doc = SimpleDocTemplate(
        flocation, rightMargin=15, leftMargin=15, topMargin=0, bottomMargin=0
    )
    styles = getSampleStyleSheet()

    Story = [Spacer(1, 0.5)]
    Story.append(Spacer(1, 0.4 * inch))
    style = styles["Normal"]

    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 12
    normal.leading = 18
    title = "<b>EZOD UNIVERSITY OF TECHNOLOGY, ADAMA</b>"  # TODO: Make this dynamic
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    style = getSampleStyleSheet()

    school = style["Normal"]
    school.alignment = TA_CENTER
    school.fontName = "Helvetica"
    school.fontSize = 10
    school.leading = 18
    school_title = (
        "<b>SCHOOL OF ELECTRICAL ENGINEERING & COMPUTING</b>"  # TODO: Make this dynamic
    )
    school_title = Paragraph(school_title.upper(), school)
    Story.append(school_title)

    style = getSampleStyleSheet()
    Story.append(Spacer(1, 0.1 * inch))
    department = style["Normal"]
    department.alignment = TA_CENTER
    department.fontName = "Helvetica"
    department.fontSize = 9
    department.leading = 18
    department_title = (
        "<b>DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING</b>"  # TODO: Make this dynamic
    )
    department_title = Paragraph(department_title, department)
    Story.append(department_title)
    Story.append(Spacer(1, 0.3 * inch))

    title = "<b><u>STUDENT COURSE REGISTRATION FORM</u></b>"
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    student = Student.objects.get(student__pk=request.user.id)

    tbl_data = [
        [
            Paragraph(
                "<b>Registration Number : " + request.user.username.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Name : " + request.user.get_full_name.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Session : " + current_session.session.upper() + "</b>",
                styles["Normal"],
            ),
            Paragraph("<b>Level: " + student.level + "</b>", styles["Normal"]),
        ],
    ]
    tbl = Table(tbl_data)
    Story.append(tbl)
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>FIRST SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    # FIRST SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph("Name, Siganture of course lecturer & Date", style["Normal"]),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    first_semester_unit = 0
    for course in courses:
        if course.course.semester == settings.FIRST:
            first_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second First Credit : " + str(first_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    # FIRST SEMESTER ENDS HERE
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>SECOND SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)
    # SECOND SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph(
                "<b>Name, Signature of course lecturer & Date</b>", style["Normal"]
            ),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    second_semester_unit = 0
    for course in courses:
        if course.course.semester == settings.SECOND:
            second_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            # color = colors.black
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second Semester Credit : " + str(second_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    Story.append(Spacer(1, 2))
    style = getSampleStyleSheet()
    certification = style["Normal"]
    certification.alignment = TA_JUSTIFY
    certification.fontName = "Helvetica"
    certification.fontSize = 8
    certification.leading = 18
    student = Student.objects.get(student__pk=request.user.id)
    certification_text = (
        "CERTIFICATION OF REGISTRATION: I certify that <b>"
        + str(request.user.get_full_name.upper())
        + "</b>\
    has been duly registered for the <b>"
        + student.level
        + " level </b> of study in the department\
    of COMPUTER SICENCE & ENGINEERING and that the courses and credits \
    registered are as approved by the senate of the University"
    )
    certification_text = Paragraph(certification_text, certification)
    Story.append(certification_text)

    # FIRST SEMESTER ENDS HERE

    logo = settings.STATICFILES_DIRS[0] + "/img/brand.png"
    im_logo = Image(logo, 1 * inch, 1 * inch)
    setattr(im_logo, "_offs_x", -218)
    setattr(im_logo, "_offs_y", 480)
    Story.append(im_logo)

    picture = settings.BASE_DIR + request.user.get_picture()
    im = Image(picture, 1.0 * inch, 1.0 * inch)
    setattr(im, "_offs_x", 218)
    setattr(im, "_offs_y", 550)
    Story.append(im)

    doc.build(Story)
    fs = FileSystemStorage(settings.MEDIA_ROOT + "/registration_form")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname + ""
        return response
    return response
