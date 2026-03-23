export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const token = url.searchParams.get('token');

  if (!token) {
    return new Response(unsubPage('No token provided.', false), {
      status: 400, headers: { 'Content-Type': 'text/html' }
    });
  }

  const email = await env.rabbit_subscribers.get(`token:${token}`);
  if (!email) {
    return new Response(unsubPage('Token not found. Already unsubscribed, probably.', false), {
      status: 404, headers: { 'Content-Type': 'text/html' }
    });
  }

  await env.rabbit_subscribers.delete(`sub:${email}`);
  await env.rabbit_subscribers.delete(`token:${token}`);

  return new Response(unsubPage(`${email} has been removed. The rabbits will continue without you.`, true), {
    status: 200, headers: { 'Content-Type': 'text/html' }
  });
}

function unsubPage(message, success) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unsubscribed</title>
  <link href="https://fonts.googleapis.com/css?family=Press+Start+2P" rel="stylesheet">
  <style>
    body { background: #FFB7C5; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; font-family: 'Press Start 2P', monospace; }
    .box { background: #fff; padding: 40px; max-width: 480px; text-align: center; border: 4px solid #2D1B2E; box-shadow: 8px 8px 0 #2D1B2E; }
    h1 { color: ${success ? '#F5C518' : '#FF69B4'}; font-size: 1.2rem; margin-bottom: 24px; line-height: 1.8; }
    p { font-size: 0.6rem; line-height: 2.2; color: #2D1B2E; margin-bottom: 20px; }
    a { color: #FF69B4; font-size: 0.55rem; }
  </style>
</head>
<body>
  <div class="box">
    <h1>${success ? 'UNSUBSCRIBED' : 'OOPS'}</h1>
    <p>${message}</p>
    <a href="/">← back to the rabbits</a>
  </div>
</body>
</html>`;
}
