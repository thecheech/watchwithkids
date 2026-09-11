module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "public, max-age=60, s-maxage=60");
  return res.status(200).json({ 
    ok: true, 
    timestamp: new Date().toISOString() 
  });
};
