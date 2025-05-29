# THis is the file that handles code editor.
"""
Deals with running codes,
"""


from django.shortcuts import render

def editor_view(request, room_id):
    print(f" I am in thhis room {room_id}")
    return render(request,"codex/codex_home_page.html",)