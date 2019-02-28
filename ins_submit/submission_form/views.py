from django.shortcuts import render
from django.utils import timezone
from .models import Submission
from .forms import SubmissionForm
from django.shortcuts import redirect
from django.http import HttpResponseNotFound


def submission_list(request):
    submissions = Submission.objects.filter(published_date__lte=timezone.now()).order_by('published_date').reverse()
    return render(request, 'submission_form/submission_list.html', {'submissions': submissions})

def most_recent(request):
    try:
        s = Submission.objects.order_by('-published_date')[0].__dict__
    except IndexError:
        return HttpResponseNotFound('<h2>No submissions found</h2>'.format(id))
    return render(request, 'submission_form/most_recent.html', {'submission': s})

def submission_detail(request, id):
    print ('ID:  ', id)
    try:
        s = Submission.objects.filter(id=id)[0].__dict__
    except IndexError:
        return HttpResponseNotFound('<h2>Submission ID={} not found</h2>'.format(id))
    return render(request, 'submission_form/submission_detail.html', {'submission': s})


def submission_new(request):
    if request.method == "POST":
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.author = request.user
            submission.published_date = timezone.now()
            submission.publish()
            
            # Call function in CRDS to ingest delivery here:
            print ()
            print ('CALL CRDS FUNCTION HERE...')
            s = Submission.objects.order_by('-published_date')[0].__dict__
            print (s)
            print ()
            
            return redirect('most_recent')
    else:
        form = SubmissionForm()
    
    return render(request, 'submission_form/submission_edit.html', {'form': form})
