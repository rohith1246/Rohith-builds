from flask import jsonify, render_template, request, Response

from extensions import csrf
from gemini_helper import improve_prompt
from . import improve_bp


@improve_bp.route("/improve")
def improve_page() -> str:
    """Render the prompt improvement tool page."""
    return render_template("improve.html")


@improve_bp.route("/api/improve", methods=["POST"])
@csrf.exempt
def improve_prompt_api() -> Response:
    """Handle API request to optimize a user-provided prompt."""
    try:
        data: dict[str, str] | None = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        user_prompt: str | None = data.get("prompt")
        if not user_prompt:
            return jsonify({"error": "Prompt is required"}), 400
        improved: str = improve_prompt(user_prompt)
        return jsonify({"improved_prompt": improved})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

