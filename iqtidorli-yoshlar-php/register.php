<?php
require_once 'config/db.php';
$pageTitle = "Ro'yxatdan O'tish";
$error = '';
$success = '';

$regions = [
    'Toshkent shahri','Toshkent viloyati','Andijon viloyati','Farg\'ona viloyati',
    'Namangan viloyati','Samarqand viloyati','Buxoro viloyati','Navoiy viloyati',
    'Qashqadaryo viloyati','Surxondaryo viloyati','Jizzax viloyati','Sirdaryo viloyati',
    'Xorazm viloyati','Qoraqalpog\'iston Respublikasi'
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name  = trim($_POST['full_name'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $pass  = $_POST['password'] ?? '';
    $role  = $_POST['role'] ?? 'yosh';
    $region= $_POST['region'] ?? '';

    if (!$name || !$email || !$pass) {
        $error = 'Barcha maydonlarni to\'ldiring.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Email manzil noto\'g\'ri.';
    } elseif (strlen($pass) < 6) {
        $error = 'Parol kamida 6 ta belgidan iborat bo\'lishi kerak.';
    } else {
        $exists = $pdo->prepare("SELECT id FROM users WHERE email = ?");
        $exists->execute([$email]);
        if ($exists->fetch()) {
            $error = 'Bu email allaqachon ro\'yxatdan o\'tgan.';
        } else {
            $hash = password_hash($pass, PASSWORD_DEFAULT);
            $stmt = $pdo->prepare(
                "INSERT INTO users (full_name, email, password, role, region) VALUES (?,?,?,?,?)"
            );
            $stmt->execute([$name, $email, $hash, $role, $region]);
            $success = 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz! <a href="login.php">Kirish</a>';
        }
    }
}

include 'includes/header.php';
?>

<section class="auth-section">
  <div class="auth-card">
    <h2>Ro'yxatdan <span>O'tish</span></h2>
    <p class="auth-sub">Platformaga qo'shiling va iqtidoringizni namoyish eting</p>

    <?php if ($error): ?>
      <div class="alert alert-error"><?= $error ?></div>
    <?php endif; ?>
    <?php if ($success): ?>
      <div class="alert alert-success"><?= $success ?></div>
    <?php endif; ?>

    <form method="POST" action="">
      <div class="form-group">
        <label>To'liq Ism</label>
        <input type="text" name="full_name" placeholder="Ism Familiya"
               value="<?= htmlspecialchars($_POST['full_name'] ?? '') ?>" required/>
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" placeholder="email@example.com"
               value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required/>
      </div>
      <div class="form-group">
        <label>Parol</label>
        <input type="password" name="password" placeholder="Kamida 6 ta belgi" required/>
      </div>
      <div class="form-group">
        <label>Viloyat</label>
        <select name="region">
          <option value="">— Tanlang —</option>
          <?php foreach ($regions as $r): ?>
            <option value="<?= $r ?>" <?= (($_POST['region'] ?? '') === $r) ? 'selected' : '' ?>>
              <?= $r ?>
            </option>
          <?php endforeach; ?>
        </select>
      </div>
      <div class="form-group">
        <label>Rol</label>
        <select name="role">
          <option value="yosh">🧑‍💻 Iqtidorli Yosh</option>
          <option value="mentor">👨‍🏫 Mentor</option>
          <option value="investor">💼 Investor</option>
        </select>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;justify-content:center;">
        Ro'yxatdan O'tish
      </button>
    </form>
    <p class="auth-link">Allaqachon hisobingiz bormi? <a href="login.php">Kirish</a></p>
  </div>
</section>

<?php include 'includes/footer.php'; ?>
