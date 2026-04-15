<?php
require_once 'config/db.php';
$pageTitle = 'Kirish';
$error = '';

if (isLoggedIn()) {
    header('Location: profile.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    $pass  = $_POST['password'] ?? '';

    if (!$email || !$pass) {
        $error = 'Email va parolni kiriting.';
    } else {
        $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$email]);
        $user = $stmt->fetch();

        if ($user && password_verify($pass, $user['password'])) {
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['user']    = $user;
            header('Location: profile.php');
            exit;
        } else {
            $error = 'Email yoki parol noto\'g\'ri.';
        }
    }
}

include 'includes/header.php';
?>

<section class="auth-section">
  <div class="auth-card">
    <h2>Tizimga <span>Kirish</span></h2>
    <p class="auth-sub">Hisobingizga kiring va davom eting</p>

    <?php if ($error): ?>
      <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <form method="POST" action="">
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" placeholder="email@example.com"
               value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required/>
      </div>
      <div class="form-group">
        <label>Parol</label>
        <input type="password" name="password" placeholder="Parolingiz" required/>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;justify-content:center;">
        Kirish
      </button>
    </form>
    <p class="auth-link">Hisobingiz yo'qmi? <a href="register.php">Ro'yxatdan o'tish</a></p>
  </div>
</section>

<?php include 'includes/footer.php'; ?>
