/* =====================================================================
   ADHD-VISION AUTHENTICATION MANAGEMENT MODULE
   ==================================================================== */

const Auth = {
  /**
   * Check if evaluator is logged in
   */
  isLoggedIn() {
    return localStorage.getItem('evaluador') !== null;
  },

  /**
   * Get current evaluator data
   */
  getEvaluador() {
    const data = localStorage.getItem('evaluador');
    try {
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('Error parsing session data', e);
      return null;
    }
  },

  /**
   * Store evaluator session upon login
   */
  login(evaluadorObj) {
    localStorage.setItem('evaluador', JSON.stringify(evaluadorObj));
  },

  /**
   * Terminate user session
   */
  logout() {
    localStorage.removeItem('evaluador');
    // Redirect or trigger router redraw
    window.location.reload();
  }
};
