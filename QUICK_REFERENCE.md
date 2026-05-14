# 🎯 QUICK REFERENCE - Professional E-Service UI System

## 📋 CSS Classes - Quick Reference

### Layout
```html
<div class="container"><!-- Max 1200px centered --></div>
<div class="container-sm"><!-- Max 640px --></div>
<div class="container-md"><!-- Max 768px --></div>
<div class="container-lg"><!-- Max 1024px --></div>
```

### Grid Systems
```html
<!-- Auto-fit grid -->
<div class="grid grid-2"><!-- 2+ columns --></div>
<div class="grid grid-3"><!-- 3+ columns --></div>
<div class="grid grid-4"><!-- 4+ columns --></div>
```

### Flexbox Utilities
```html
<div class="flex"><!-- display: flex --></div>
<div class="flex-center"><!-- centered both ways --></div>
<div class="flex-between"><!-- space-between --></div>
<div class="flex-column"><!-- flex-direction: column --></div>
<div class="flex-wrap"><!-- flex-wrap --></div>
```

### Spacing (Gap)
```html
<div class="gap-1">8px gap</div>
<div class="gap-2">12px gap</div>
<div class="gap-3">16px gap</div>
<div class="gap-4">20px gap</div>
<div class="gap-5">24px gap</div>
<div class="gap-6">28px gap</div>
```

### Padding/Margin
```html
<!-- Padding -->
<div class="p-1">8px</div> <div class="p-2">12px</div> <div class="p-3">16px</div>
<div class="p-4">20px</div> <div class="p-5">24px</div>

<!-- Margin -->
<div class="m-1">8px</div> <div class="m-2">12px</div> <div class="m-3">16px</div>

<!-- Margin Top -->
<div class="mt-1">8px</div> <div class="mt-2">12px</div> <div class="mt-3">16px</div>

<!-- Margin Bottom -->
<div class="mb-1">8px</div> <div class="mb-2">12px</div> <div class="mb-3">16px</div>
```

---

## 🎨 Buttons

### Basic Buttons
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-danger">Danger</button>
<button class="btn btn-warning">Warning</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>
```

### Button Sizes
```html
<button class="btn btn-sm">Small</button>
<button class="btn">Default</button>
<button class="btn btn-lg">Large</button>
```

### Special Buttons
```html
<button class="btn btn-full">Full Width</button>
<button class="btn btn-icon">💬</button> <!-- Circular 40x40 -->
```

---

## 🎴 Cards

### Basic Card
```html
<div class="card">
    <div class="card-header">
        <h3>Title</h3>
    </div>
    <div class="card-body">Content goes here</div>
    <div class="card-footer">Actions</div>
</div>
```

### Stat Card
```html
<div class="stat-card">
    <div class="stat-icon">📊</div>
    <div class="stat-label">Requests</div>
    <div class="stat-value">1,234</div>
    <div class="stat-change">↑ 12% this month</div>
</div>
```

---

## 🏷️ Badges & Status

### Badges
```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-secondary">Secondary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-danger">Danger</span>
<span class="badge badge-warning">Warning</span>
```

### Status Badges
```html
<span class="status-badge status-pending">Pending</span>
<span class="status-badge status-approved">Approved</span>
<span class="status-badge status-rejected">Rejected</span>
<span class="status-badge status-inprogress">In Progress</span>
<span class="status-badge status-completed">Completed</span>
```

---

## 📝 Forms

### Form Group
```html
<div class="form-group">
    <label for="email">Email Address</label>
    <input type="email" id="email" required>
    <div class="form-help">We'll keep this private</div>
</div>
```

### Form States
```html
<input type="text">           <!-- Normal -->
<input type="text" disabled>  <!-- Disabled -->
<input type="text" required>  <!-- Required -->
```

### Form Errors
```html
<div class="form-group">
    <label>Password</label>
    <input type="password">
    <div class="form-error">Password is required</div>
</div>
```

---

## 📊 Tables

### Basic Table
```html
<table>
    <thead>
        <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>John Doe</td>
            <td>john@example.com</td>
            <td><span class="status-badge status-approved">Active</span></td>
        </tr>
    </tbody>
</table>
```

---

## 🎯 Alerts & Notifications

### Alert Messages
```html
<div class="alert alert-success">✓ Operation successful!</div>
<div class="alert alert-error">✗ Something went wrong</div>
<div class="alert alert-warning">⚠ Please review this</div>
<div class="alert alert-info">ℹ For your information</div>
```

### Toast Notifications (JavaScript)
```javascript
Toast.show('Success message', 'success', 3000);
Toast.show('Error occurred', 'error', 3000);
Toast.show('Warning!', 'warning', 3000);
Toast.show('Info', 'info', 3000);
```

---

## 🎬 Animations

### Add Animations
```html
<!-- Fade in -->
<div class="animate-fade-in">Content</div>

<!-- Fade in and up -->
<div class="animate-fade-in-up">Content</div>

<!-- Slide from left -->
<div class="animate-slide-in-left">Content</div>

<!-- Scale in -->
<div class="animate-scale-in">Content</div>

<!-- Float animation -->
<div class="animate-float">Content</div>
```

---

## 🔤 Typography

### Text Colors
```html
<p class="text-primary">Primary text</p>
<p class="text-secondary">Secondary text</p>
<p class="text-muted">Muted text</p>
<p class="text-danger">Danger text</p>
<p class="text-success">Success text</p>
<p class="text-warning">Warning text</p>
```

### Text Sizes
```html
<p class="text-sm">Small text</p>
<p>Normal text</p>
<p class="text-lg">Large text</p>
<p class="text-xl">Extra large text</p>
```

### Font Weights
```html
<p class="font-normal">Regular</p>
<p class="font-semibold">Semibold</p>
<p class="font-bold">Bold</p>
```

### Text Alignment
```html
<p class="text-left">Left aligned</p>
<p class="text-center">Center aligned</p>
<p class="text-right">Right aligned</p>
```

---

## 🖼️ Backgrounds

### Background Colors
```html
<div class="bg-primary">Primary bg</div>
<div class="bg-secondary">Secondary bg</div>
<div class="bg-tertiary">Tertiary bg</div>
<div class="bg-dark">Dark bg</div>
```

---

## 👁️ Visibility & Display

### Display
```html
<div class="hidden">Hidden element</div>
<div class="visible">Visible element</div>
```

### Opacity
```html
<div class="opacity-50">50% opacity</div>
<div class="opacity-75">75% opacity</div>
```

---

## 📐 Borders & Shadows

### Borders
```html
<div class="border-top">Top border</div>
<div class="border-bottom">Bottom border</div>
<div class="border-left">Left border</div>
<div class="border-right">Right border</div>
```

### Border Radius
```html
<div class="rounded">6px radius</div>
<div class="rounded-lg">12px radius</div>
<div class="rounded-full">Circular</div>
```

### Shadows
```html
<div class="shadow">Small shadow</div>
<div class="shadow-md">Medium shadow</div>
<div class="shadow-lg">Large shadow</div>
```

---

## 📱 Responsive Classes

### Responsive Columns
```html
<!-- Mobile: 1 column, Desktop: 2 columns -->
<div class="grid grid-2">
    <div>Column 1</div>
    <div>Column 2</div>
</div>
```

### Mobile Utilities
```html
<div class="flex-column-mobile">Vertical on mobile</div>
```

---

## 🎛️ JavaScript Utilities

### Toast Notifications
```javascript
// Show message for 3 seconds
Toast.show('Welcome!', 'success');

// Custom duration
Toast.show('Error!', 'error', 5000);
```

### Modal Dialogs
```javascript
// Create modal
const modal = new Modal('#my-modal');

// Open modal
modal.open();

// Close modal
modal.close();

// Toggle modal
modal.toggle();
```

### Data Tables
```javascript
// Create sortable, filterable table
const table = new DataTable('#my-table');

// Click headers to sort
// Use [data-filter] inputs to filter
```

### Utility Functions
```javascript
// Debounce (e.g., search input)
const search = debounce((query) => {
    console.log(query);
}, 300);

// Throttle (e.g., scroll events)
const onScroll = throttle(() => {
    console.log('scrolling');
}, 1000);

// Format currency (₹)
formatCurrency(1000); // ₹1,000.00

// Format date
formatDate('2026-04-29'); // April 29, 2026
```

---

## 🚀 Common Patterns

### Service Card
```html
<div class="card animate-fade-in-up">
    <img src="..." loading="lazy">
    <div class="card-body">
        <h3>Service Name</h3>
        <p>Description</p>
        <div class="flex-between gap-3">
            <span class="badge badge-primary">₹999</span>
            <a href="#" class="btn btn-sm btn-primary">Apply</a>
        </div>
    </div>
</div>
```

### Dashboard Section
```html
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-label">Total</div>
        <div class="stat-value">1,234</div>
    </div>
    <!-- More stat cards -->
</div>
```

### Hero Section
```html
<section class="hero">
    <div class="container">
        <h1>Welcome to Our Platform</h1>
        <p>Professional service management</p>
        <a href="#" class="btn btn-primary">Get Started</a>
    </div>
</section>
```

### Navigation
```html
<nav class="navbar">
    <div class="container">
        <div class="navbar-inner">
            <a href="/" class="navbar-brand">Logo</a>
            <div class="navbar-nav">
                <a href="/">Home</a>
                <a href="/services">Services</a>
                <a href="/contact">Contact</a>
            </div>
        </div>
    </div>
</nav>
```

---

## ✨ Pro Tips

1. **Always use containers** for consistency
   ```html
   <div class="container">Your content</div>
   ```

2. **Use semantic HTML**
   ```html
   <button>Not <div></div></button>
   ```

3. **Combine utility classes**
   ```html
   <div class="flex flex-center gap-3">
       <h2>Title</h2>
       <p>Subtitle</p>
   </div>
   ```

4. **Keep animations subtle** (300-600ms)
   ```css
   animation: fadeInUp 0.3s ease-out;
   ```

5. **Test on mobile devices** regularly
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```

---

**For complete documentation, see:** `TRANSFORMATION_GUIDE.md`

**Last Updated:** April 2026
