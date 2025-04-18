# Imsdly Landing Page Development Guide

## Overview
This guide outlines the development of a landing page for Imsdly, a PyQt file transfer application currently in development (at step 10 of the ADG). The landing page will serve as the product's web presence, offering information about the application, user authentication, pricing details, newsletter signup, and community engagement.

## Tech Stack
- **Frontend**: React with Next.js
- **UI Components**: shadcn/ui
- **Authentication**: Supabase Auth
- **Database**: Supabase for user data and licenses
- **Deployment**: Vercel

## Phase 1: Setup & Basic Structure

### Step 1: Project Setup
1.1. Create a new Next.js project with TypeScript
```bash
npx create-next-app@latest imsdly-landing --typescript
```

1.2. Set up shadcn/ui
```bash
npx shadcn-ui@latest init
```

1.3. Configure Supabase
- Create a Supabase project
- Save API keys in .env.local
```
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

1.4. Install additional dependencies
```bash
npm install @supabase/auth-helpers-nextjs @supabase/supabase-js react-hook-form zod @hookform/resolvers
```

## Phase 2: Components & Layout

### Step 2: Header & Navigation
2.1. Create responsive navbar with:
- Logo
- Product link
- Features link
- Pricing link
- Community link
- Sign In / Sign Up buttons

2.2. Implement mobile navigation with hamburger menu

### Step 3: Hero Section
3.1. Create an eye-catching hero section with:
- Compelling headline about Imsdly
- Subheading describing core purpose
- Main CTA button ("Get Started" or "Join Beta")
- Secondary CTA for more information
- Application screenshot or illustration

3.2. Add subtle animation for visual engagement

### Step 4: Product Information
4.1. Implement a features section highlighting core functionality:
- SD card media transfer
- Automatic card detection
- File organization by date or custom structure
- Batch file renaming
- File filtering capabilities

4.2. Create a "How It Works" section with step-by-step process
- Step 1: Connect SD card
- Step 2: Select files
- Step 3: Choose destination and organization
- Step 4: Transfer files

4.3. Add visual indicators showing current development progress (Step 10 of 17)

## Phase 3: Authentication & User Management

### Step 5: Authentication Components
5.1. Create sign-up form with Supabase Auth
- Email field
- Password field with strength indicator
- Name fields
- Agreement to terms and privacy policy
- Sign-up button

5.2. Implement sign-in form
- Email/username field
- Password field
- "Remember me" option
- Forgot password link
- Sign-in button

5.3. Add social authentication options (Google, GitHub) if desired

### Step 6: User Dashboard (Protected Route)
6.1. Create a basic dashboard layout for authenticated users
- Sidebar navigation
- Account details section
- License management section
- User preferences

6.2. Implement Supabase RLS policies for secure data access

### Step 7: License Management
7.1. Create database tables for license management
```sql
CREATE TABLE licenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  license_key TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,
  type TEXT NOT NULL,
  status TEXT NOT NULL
);
```

7.2. Build license creation and assignment functionality
7.3. Implement license verification system
7.4. Create admin interface for license management (optional)

## Phase 4: Pricing & Payment

### Step 8: Pricing Component
8.1. Design pricing card components with:
- Free tier (limited features)
- Standard tier (full features)
- Pro tier (advanced features)

8.2. Include feature comparison table

8.3. Clearly mark features that are still in development

### Step 9: Payment Integration
9.1. Set up Stripe integration for payment processing
9.2. Create checkout flow
9.3. Implement webhook for successful payments
9.4. Set up license generation upon payment completion

## Phase 5: Community & Engagement

### Step 10: Newsletter Signup
10.1. Create newsletter component with:
- Email input field
- GDPR-compliant checkbox
- Subscribe button
- Benefits description

10.2. Connect to email service (Mailchimp, ConvertKit, etc.)
10.3. Implement double opt-in flow
10.4. Create confirmation and thank you UI

### Step 11: Community Section
11.1. Build community engagement section
- GitHub repository link
- Discord/Slack community invitation
- Contribution guidelines
- Development roadmap showing progress

11.2. Create a developer-focused "Get Involved" form
- Skills/expertise fields
- Areas of interest dropdown
- Contact information
- Message/proposal field

11.3. Set up Supabase table to store community applications

## Phase 6: Polish & Launch

### Step 12: SEO & Performance
12.1. Implement SEO best practices
- Metadata for all pages
- OpenGraph tags
- Structured data
- Sitemap generation

12.2. Optimize performance
- Implement image optimization
- Add lazy loading for components
- Audit and improve loading speed

### Step 13: Legal & Compliance
13.1. Create necessary legal pages
- Terms of Service
- Privacy Policy
- Cookie Policy
- GDPR compliance measures

13.2. Implement cookie consent banner

### Step 14: Testing & Deployment
14.1. Conduct thorough testing
- Cross-browser compatibility
- Mobile responsiveness
- Authentication flows
- Payment processes

14.2. Set up CI/CD pipeline with GitHub Actions
14.3. Deploy to Vercel
14.4. Configure custom domain and SSL

## Content Guidelines

### Product Description
Focus on solving the specific pain points:
- Disorganized media files
- Time-consuming manual transfer
- Inconsistent file naming
- Difficulty finding specific files

Example headline: "Streamline your media workflow with Imsdly"

### Development Status Communication
Be transparent about the current status:
- "Currently in active development (Stage 10/17)"
- "Join early for exclusive beta access"
- "Help shape the future of Imsdly"

### Pricing Strategy
Consider a tiered approach:
- **Early Adopter**: Discounted lifetime access
- **Standard**: Regular price with all features
- **Pro**: Premium features (future development)

## Design Guidelines

### Color Palette
- Primary: #0078d7 (Blue)
- Secondary: #333333 (Dark Gray)
- Accent: #ff9900 (Orange)
- Background: #f5f7fa (Light Gray)
- Text: #222222 (Near Black)

### Typography
- Headings: Inter (Bold)
- Body: Inter (Regular)
- Code: JetBrains Mono

### Visual Style
- Clean, modern interface
- Subtle animations for interactions
- Dark/light mode toggle
- Professional with slight tech aesthetic

## Implementation Checklist

- [ ] Next.js project setup
- [ ] shadcn/ui components integration
- [ ] Responsive layout implementation
- [ ] Supabase auth integration
- [ ] User dashboard creation
- [ ] License management system
- [ ] Pricing component
- [ ] Payment processing
- [ ] Newsletter signup
- [ ] Community engagement section
- [ ] SEO optimization
- [ ] Legal compliance
- [ ] Testing across devices
- [ ] Deployment and monitoring 