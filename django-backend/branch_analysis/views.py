"""
Branch Transfer Analysis Views

Client-side CSV processing tool for analyzing branch-to-branch transfers by buyline.
No server-side processing - all analysis happens in the browser for speed and privacy.
"""

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def branch_transfer_analysis(request):
    """
    Main branch transfer analysis page
    Renders upload interface and analysis tools
    """
    if not request.session.get('customer_logged_in'):
        return redirect('/login/')

    return render(request, 'branch_analysis/transfer_analysis.html')
