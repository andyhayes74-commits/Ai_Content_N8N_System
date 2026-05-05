INSERT INTO client_profiles (client_code, client_name, preferred_tone, industry, compliance_notes)
VALUES
('demo-fitness', 'Demo Fitness Co', 'motivational, concise', 'fitness', 'No medical claims without source.'),
('demo-saas', 'Demo SaaS Labs', 'clear, practical', 'software', 'Avoid guarantee language.')
ON CONFLICT (client_code) DO NOTHING;
