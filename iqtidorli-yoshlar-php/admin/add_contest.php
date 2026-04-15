<?php
require_once '../config/db.php';
if (!isLoggedIn() || currentUser()['role'] !== 'admin') {
    header('Location: ../index.php');
    exit;
}
$pageTitle = 'Tanlov Qo\'shish';
$msg = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $title = trim($_POST['title'] ?? '');
    $desc  = trim($_POST['description'] ?? '');
    $dead  = $_POST['deadline'] ?? null;
    $prize = trim($_POST['prize'] ?? '');

    if ($title) {
        $pdo->prepare("INSERT INTO contests (title, description, deadline, prize) VALUES (?,?,?,?)")
            ->execute([$title, $desc, $dead ?: null, $prize]);
        $msg = 'Tanlov muvaffaqiyatli qo\'shildi.';
    }
}

include '../includes/header.php';
?>

<section class="auth-section">
  <div class="auth-card">
    <h2>Yangi <span>Tanlov Qo'shish</span></h2>

    <?php if ($msg): ?>
      <div class="alert alert-success"><?= $msg ?> <a href="../contests.php">Ko'rish</a></div>
    <?php endif; ?>

    <form method="POST">
      <div class="form-group">
        <label>Tanlov Nomi</label>
        <input type="text" name="title" required placeholder="Tanlov nomi"/>
      </div>
      <div class="form-group">
        <label>Tavsif</label>
        <textarea name="description" rows="4" placeholder="Tanlov haqida ma'lumot"></textarea>
      </div>
      <div class="form-group">
        <label>Muddat</label>
        <input type="date" name="deadline"/>
      </div>
      <div class="form-group">
        <label>Mukofot</label>
        <input type="text" name="prize" placeholder="Masalan: 50,000,000 so'm"/>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;justify-content:center;">Qo'shish</button>
    </form>
    <p class="auth-link"><a href="dashboard.php">← Dashboard</a></p>
  </div>
</section>

<?php include '../includes/footer.php'; ?>
