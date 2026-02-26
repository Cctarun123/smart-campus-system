import {
  Bell,
  Settings,
  LayoutDashboard,
  Utensils,
  Heart,
  MessageCircle,
  History,
  Receipt,
  Crown,
  Search,
  Croissant,
  Beef,
  CupSoda,
  Drumstick,
  Pizza,
  Fish,
  MapPin,
  Wallet,
  ChevronRight,
  Plus,
} from "lucide-react";

const sidebarItems = [
  { label: "Dashboard", icon: LayoutDashboard, active: true },
  { label: "Food Order", icon: Utensils },
  { label: "Favorite", icon: Heart },
  { label: "Messages", icon: MessageCircle },
  { label: "Order History", icon: History },
  { label: "Bills", icon: Receipt },
  { label: "Settings", icon: Settings },
];

const categories = [
  { label: "Bakery", icon: Croissant },
  { label: "Burger", icon: Beef },
  { label: "Beverage", icon: CupSoda },
  { label: "Chicken", icon: Drumstick },
  { label: "Pizza", icon: Pizza },
  { label: "Seafood", icon: Fish },
];

const dishes = [
  {
    title: "Classic Cheese Burger",
    image:
      "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
    rating: 4.8,
    price: 8.9,
  },
  {
    title: "Spicy Crispy Chicken",
    image:
      "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=80",
    rating: 4.7,
    price: 11.2,
  },
  {
    title: "Italian Pepperoni Pizza",
    image:
      "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=900&q=80",
    rating: 4.9,
    price: 13.4,
  },
  {
    title: "Fresh Berry Smoothie",
    image:
      "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80",
    rating: 4.6,
    price: 6.75,
  },
];

const recentOrders = [
  "https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1608039755401-742074f0548d?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1618164436241-4473940d1f5c?auto=format&fit=crop&w=900&q=80",
];

const orderItems = [
  { name: "Cheese Burger", qty: 1, price: 8.9 },
  { name: "Chicken Bucket", qty: 1, price: 11.2 },
  { name: "Orange Juice", qty: 2, price: 7.0 },
];

const subtotal = orderItems.reduce((sum, item) => sum + item.price, 0);
const delivery = 2.5;
const total = subtotal + delivery;

function Stars({ rating }) {
  return (
    <div className="text-sm tracking-wide text-amber-500">{"?????"} <span className="text-slate-500">({rating})</span></div>
  );
}

export default function FoodPreOrderDashboard() {
  return (
    <div className="min-h-screen bg-ui-bg p-5 lg:p-8">
      <div className="mx-auto grid w-full max-w-[1540px] grid-cols-12 gap-6">
        <aside className="col-span-12 rounded-3xl bg-white p-5 shadow-soft lg:col-span-2 lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)] lg:flex lg:flex-col">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">GoMeal</h1>
            <p className="mt-1 text-xs text-slate-500">Premium Food Ordering</p>
          </div>

          <nav className="mt-7 space-y-2">
            {sidebarItems.map(({ label, icon: Icon, active }) => (
              <button
                key={label}
                className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-medium transition ${
                  active
                    ? "bg-gradient-to-r from-brand-400 to-brand-500 text-white shadow-card"
                    : "text-slate-600 hover:bg-amber-50 hover:text-slate-900"
                }`}
              >
                <Icon size={17} />
                {label}
              </button>
            ))}
          </nav>

          <div className="mt-6 rounded-3xl bg-gradient-to-br from-brand-400 to-brand-500 p-4 text-white lg:mt-auto">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider">Upgrade</span>
              <Crown size={16} />
            </div>
            <p className="mt-2 text-sm font-medium leading-relaxed">Get premium meal deals and express delivery access.</p>
            <button className="mt-3 rounded-xl bg-white/25 px-3 py-2 text-xs font-semibold">Upgrade Now</button>
          </div>
        </aside>

        <main className="col-span-12 space-y-6 lg:col-span-7">
          <header className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Hello, User</h2>
              <p className="text-sm text-slate-500">Ready for your next meal?</p>
            </div>

            <div className="flex items-center gap-3">
              <button className="rounded-full bg-white p-2.5 shadow-card text-slate-600"><Bell size={18} /></button>
              <button className="rounded-full bg-white p-2.5 shadow-card text-slate-600"><Settings size={18} /></button>
              <img
                src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&q=80"
                alt="Profile"
                className="h-10 w-10 rounded-full object-cover shadow-card"
              />
            </div>
          </header>

          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="What do you want eat today..."
              className="w-full rounded-2xl border-0 bg-white py-3.5 pl-11 pr-4 text-sm shadow-card ring-1 ring-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-400 via-amber-300 to-brand-500 p-6 shadow-soft">
            <div className="relative z-10 max-w-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-amber-900/80">Special Offer</p>
              <h3 className="mt-2 text-2xl font-semibold text-slate-900">Get Discount Voucher Up To 20%</h3>
              <button className="mt-4 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Order Now</button>
            </div>
            <img
              src="https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=900&q=80"
              alt="Happy person holding food"
              className="absolute -right-3 bottom-0 h-full max-h-44 rounded-2xl object-cover sm:max-h-48"
            />
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Category</h3>
              <button className="flex items-center gap-1 text-sm font-medium text-brand-700">See all <ChevronRight size={15} /></button>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
              {categories.map(({ label, icon: Icon }) => (
                <button key={label} className="rounded-2xl bg-white p-4 text-left shadow-card transition hover:-translate-y-0.5">
                  <div className="mb-2 inline-flex rounded-xl bg-amber-50 p-2 text-brand-700">
                    <Icon size={18} />
                  </div>
                  <p className="text-sm font-medium text-slate-700">{label}</p>
                </button>
              ))}
            </div>
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Popular Dishes</h3>
              <button className="text-sm font-medium text-brand-700">See all</button>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {dishes.map((dish) => (
                <article key={dish.title} className="rounded-3xl bg-white p-3 shadow-card">
                  <div className="relative">
                    <img src={dish.image} alt={dish.title} className="h-44 w-full rounded-2xl object-cover" />
                    <span className="absolute left-3 top-3 rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-brand-700 shadow">15% off</span>
                  </div>
                  <div className="mt-3 flex items-end justify-between gap-2">
                    <div>
                      <h4 className="font-semibold text-slate-900">{dish.title}</h4>
                      <Stars rating={dish.rating} />
                      <p className="mt-1 text-base font-semibold text-slate-900">${dish.price.toFixed(2)}</p>
                    </div>
                    <button className="inline-flex items-center gap-1 rounded-xl bg-gradient-to-r from-brand-400 to-brand-500 px-3 py-2 text-sm font-semibold text-white">
                      <Plus size={16} /> Add
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Recent Orders</h3>
              <button className="text-sm font-medium text-brand-700">View all</button>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {recentOrders.map((img, idx) => (
                <div key={img} className="rounded-2xl bg-white p-2 shadow-card">
                  <img src={img} alt={`Recent order ${idx + 1}`} className="h-24 w-full rounded-xl object-cover" />
                </div>
              ))}
            </div>
          </section>
        </main>

        <aside className="col-span-12 space-y-5 lg:col-span-3">
          <section className="rounded-3xl bg-white p-5 shadow-soft">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">Wallet Balance</h3>
              <Wallet size={18} className="text-brand-700" />
            </div>
            <p className="mt-3 text-3xl font-semibold text-slate-900">$148.75</p>
            <p className="mt-1 text-xs text-slate-500">Available for quick checkout</p>
          </section>

          <section className="rounded-3xl bg-white p-5 shadow-soft">
            <h3 className="text-base font-semibold">Delivery Address</h3>
            <div className="mt-3 flex gap-3 rounded-2xl bg-slate-50 p-3">
              <MapPin size={18} className="mt-0.5 text-brand-700" />
              <p className="text-sm text-slate-600">Block 34, LPU Campus, Jalandhar, Punjab 144411</p>
            </div>
          </section>

          <section className="rounded-3xl bg-white p-5 shadow-soft">
            <h3 className="text-base font-semibold">Order Summary</h3>

            <div className="mt-4 space-y-3">
              {orderItems.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-sm">
                  <p className="text-slate-600">{item.qty}x {item.name}</p>
                  <p className="font-medium text-slate-900">${item.price.toFixed(2)}</p>
                </div>
              ))}
            </div>

            <div className="my-4 h-px bg-slate-100" />

            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span className="font-medium">${subtotal.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Delivery</span><span className="font-medium">${delivery.toFixed(2)}</span></div>
              <div className="flex justify-between text-base"><span className="font-semibold">Total</span><span className="font-semibold">${total.toFixed(2)}</span></div>
            </div>

            <input
              type="text"
              placeholder="Apply coupon code"
              className="mt-4 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />

            <button className="mt-4 w-full rounded-2xl bg-gradient-to-r from-brand-400 to-brand-500 px-4 py-3 text-sm font-semibold text-slate-900 shadow-card">
              Checkout
            </button>
          </section>
        </aside>
      </div>
    </div>
  );
}
