<?php
require_once 'config/db.php';
$pageTitle = 'Tanlovlar va Grantlar';

$contests = $pdo->query("SELECT * FROM contests ORDER BY deadline ASC")->fetchAll();

include 'includes/header.php';
?>

<section style="padding-top:120px;">
  <div class="section-title">
    <h2>Tanlovlar va <span>Grantlar</span></h2>
    <p>Davlat va xususiy sektor tomonidan e'lon qilingan imkoniyatlar</p>
  </div>

  <?php if (isLoggedIn() && currentUser()['role'] === 'admin'): ?>
    <div style="text-align:center;margin-bottom:32px;">
      <a href="admin/add_contest.php" class="btn-primary">+ Yangi Tanlov Qo'shish</a>
    </div>
  <?php endif; ?>

  <div class="features-grid" style="max-width:1100px;margin:0 auto;">
    <?php if ($contests): ?>
      <?php foreach ($contests as $c): ?>
        <div class="feature-card">
          <div class="feature-icon">🏆</div>
          <h3><?= htmlspecialchars($c['title']) ?></h3>
          <p><?= htmlspecialchars($c['description'] ?? '') ?></p>
          <div style="margin-top:14px;display:flex;flex-direction:column;gap:6px;">
            <?php if ($c['deadline']): ?>
              <span style="font-size:.82rem;color:var(--accent);">
                📅 Muddat: <?= date('d.m.Y', strtotime($c['deadline'])) ?>
              </span>
            <?php endif; ?>
            <?php if ($c['prize']): ?>
              <span style="font-size:.82rem;color:#FFD700;">
                💰 Mukofot: <?= htmlspecialchars($c['prize']) ?>
              </span>
            <?php endif; ?>
          </div>
          <?php if (isLoggedIn()): ?>
            <a href="#" class="btn-primary" style="margin-top:14px;display:inline-block;padding:8px 20px;font-size:.85rem;">
              Ariza Topshirish
            </a>
          <?php else: ?>
            <a href="login.php" class="btn-outline" style="margin-top:14px;display:inline-block;padding:8px 20px;font-size:.85rem;">
              Kirish kerak
            </a>
          <?php endif; ?>
        </div>
      <?php endforeach; ?>
    <?php else: ?>
      <p style="color:var(--muted);text-align:center;padding:40px;">Hozircha tanlov yo'q.</p>
    <?php endif; ?>
  </div>
</section>

<?php include 'includes/footer.php'; ?>
