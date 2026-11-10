def what_if_panel() -> str:
    return """
<div class="what-if" id="degree-what-if">
  <div class="what-if-heading">
    <div><h4>What if?</h4><p>Try adding a course directly or swapping out one scheduled course.</p></div>
  </div>
  <div class="what-if-controls">
    <label>Course<select class="what-if-course"></select></label>
    <label>Semester<select class="what-if-semester"></select></label>
    <label>Change<select class="what-if-swap"></select></label>
  </div>
  <div class="what-if-result" role="status" aria-live="polite"></div>
  <script type="application/json" class="what-if-data">{}</script>
</div>
"""
