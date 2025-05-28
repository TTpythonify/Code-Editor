# THis is the file that handles code editor.
"""
Deals with running codes,
"""


from django.shortcuts import render

def editor_view(request):
    return render(request, 'codex/codex_code_editor.html')



