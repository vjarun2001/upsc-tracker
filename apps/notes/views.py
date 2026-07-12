from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteForm
from .models import Note


@login_required
def note_list(request):
    notes = Note.objects.filter(user=request.user).select_related("subject", "topic")

    return render(
        request,
        "notes/list.html",
        {
            "notes": notes,
            "form": NoteForm(user=request.user),
        },
    )


@login_required
def add_note(request):
    if request.method == "POST":

        form = NoteForm(request.POST, user=request.user)

        if form.is_valid():

            note = form.save(commit=False)
            note.user = request.user
            note.save()

            messages.success(request, "Note added.")

            return redirect("notes:list")

        notes = Note.objects.filter(user=request.user).select_related("subject", "topic")

        return render(request, "notes/list.html", {"notes": notes, "form": form})

    return redirect("notes:list")


@login_required
def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == "POST":

        form = NoteForm(request.POST, instance=note, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Note updated.")
            return redirect("notes:list")

    else:
        form = NoteForm(instance=note, user=request.user)

    return render(request, "notes/edit.html", {"form": form, "note": note})


@login_required
def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == "POST":
        note.delete()
        messages.success(request, "Note deleted.")

    return redirect("notes:list")
