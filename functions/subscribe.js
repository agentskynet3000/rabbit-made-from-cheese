export async function onRequestPost(context) {
  const { request, env } = context;

  let email;
  try {
    const body = await request.json();
    email = (body.email || '').trim().toLowerCase();
  } catch {
    return new Response(JSON.stringify({ error: 'invalid request' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  if (!email || !email.includes('@')) {
    return new Response(JSON.stringify({ error: 'invalid email' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  // Generate unsubscribe token
  const token = crypto.randomUUID();
  const subscriber = {
    email,
    token,
    subscribedAt: new Date().toISOString(),
  };

  await env.rabbit_subscribers.put(`sub:${email}`, JSON.stringify(subscriber));
  await env.rabbit_subscribers.put(`token:${token}`, email);

  return new Response(JSON.stringify({ ok: true, message: 'subscribed' }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  });
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }
  });
}
