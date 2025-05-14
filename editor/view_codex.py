from django.shortcuts import render



def codex_home_page(request):
    return render(request, "codex/codex_home_page.html")