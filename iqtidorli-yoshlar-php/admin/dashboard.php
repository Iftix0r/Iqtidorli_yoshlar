<?php
require_once '../config/db.php';
if (!isLoggedIn() || currentUser()['role'] !== 'admin') {
    header('Location: ../index.php');
    exit;
}
$pageTitle = 'Admin Panel';

$totalUsers    = $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn();
$totalYoshlar  = $pdo->query("SELECT COUNT(*) FROM users WHERE role='yosh'")->fetchColumn();
$totalMentors  = $pdo->query("SELECT COUNT(*) FROM users WHERE role='mentor'")->fetchColumn();
$totalContests = $pdo->query("SELECT COUNT(*) FROM contests")->fetchColumn();

$recentUsers = $pdo->query(
    "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
)->fetchAll();

// Handle score update
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['update_score'])) {
    $uid   = (int)$_POST['user_id'];
    $score = (int)$_POST['score'];
    $pdo->prepare("UPDATE users SET score=? WHERE id=?")->execute([$score, $uid]);
    header('Location: dashboard.php');
    exit;
}

include '../includes/header.php';
?>

<section style="padding-top:120px;max-width:1200px;margin:0 auto;">
  <div class="section-title">
    <h2>Admin <span>Dashboard</span></h2>
  </div>

  <!-- Stats -->
  <div class="hero-stats" style="justify-content:flex-start;margin-bottom:40px;">
    <div class="stat-item"><div class="num"><?= $totalUsers ?></div><div class="label">Jami Foydalanuvchilar</div></div>
    <div class="stat-item"><div class="num"><?= $totalYoshlar ?></div><div class="label">Iqtidorli Yoshlar</div></div>
    <div class="stat-item"><div class="num"><?= $totalMentors ?></div><div class="label">Mentorlar</div></div>
    <div class="stat-item"><div class="num"><?= $totalContests ?></div><div class="label">Tanlovlar</div></div>
  </div>

  <!-- Users table -->
  <div class="benefits-table">
    <table>
      <thead>
        <tr>
          <th>#</th><th>Ism</th><th>Email</th><th>Rol</th><th>Viloyat</th><th>Ball</th><th>Amal</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($recentUsers as $u): ?>
          <tr>
            <td><?= $u['id'] ?></td>
            <td><?= htmlspecialchars($u['full_name']) ?></td>
            <td><?= htmlspecialchars($u['email']) ?></td>
            <td><?= $u['role'] ?></td>
            <td><?= htmlspecialchars($u['region'] ?? '') ?></td>
            <td>
              <form method="POST" style="display:flex;gap:6px;align-items:center;">
                <input type="hidden" name="user_id" value="<?= $u['id'] ?>"/>
                <input type="number" name="score" value="<?= $u['score'] ?>" style="width:70px;padding:4px 8px;background:var(--card);border:1px solid rgba(108,99,255,.3);color:var(--text);border-radius:6px;"/>
                <button type="submit" name="update_score" class="btn-primary" style="padding:4px 12px;font-size:.8rem;">✓</button>
              </form>
            </td>
            <td>
              <a href="../profile.php?id=<?= $u['id'] ?>" style="color:var(--primary);font-size:.85rem;">Ko'rish</a>
            </td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>

  <div style="margin-top:24px;">
    <a href="add_contest.php" class="btn-primary">+ Yangi Tanlov Qo'shish</a>
  </div>
</section>

<?php include '../includes/footer.php'; ?>
