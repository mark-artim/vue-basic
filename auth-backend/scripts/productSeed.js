// scripts/productSeed.js
import { MongoClient } from 'mongodb';
import dotenv from 'dotenv';
dotenv.config();

const client = new MongoClient(process.env.MONGODB_URI);

const products = [
  { _id: "eclipse", name: "Eclipse ERP Extensions" },
  { _id: "ship54", name: "Ship54 - Shipping Integration" },
  { _id: "kohler", name: "Kohler Feed Tools" },
  { _id: "e54", name: "Emp54 Admin Tools" }
];

const menus = [
  { name: 'Contacts', path: '/contacts', product: 'eclipse', roles: ['contact'] },
  { name: 'Contact Change Password', path: '/contact-pw', product: 'eclipse', roles: ['contact'] },
  { name: 'Inventory Balancing', path: '/inv-bal', product: 'eclipse', roles: ['her-validation'] },
  { name: 'Customer Invoice Lookup', path: '/invoice-lookup', product: 'eclipse', roles: ['customer'] },
  { name: 'Conversion Price Validation', path: '/price-validation', product: 'eclipse', roles: ['her-validation'] },
  { name: 'Ship54 - 3rd Party Shipping', path: '/ship-station', product: 'ship54', roles: ['ship54'] },
  { name: 'Add New Vendor', path: '/vendor-add', product: 'eclipse', roles: ['her-vendor'] },
  { name: 'Kohler Feed Report', path: '/kohler-feed', product: 'kohler', roles: ['kohler'] },
  { name: 'Create Product', path: '/create-product', product: 'eclipse', roles: ['product'] },
  { name: 'API Test - Eds PN Lookup', path: '/testpage', product: 'eclipse', roles: ['admin'] },
  { name: 'e54 Companies', path: '/admin/companies', product: 'e54', roles: ['admin'] },
  { name: 'e54 Users', path: '/admin/users', product: 'e54', roles: ['admin'] },
];

async function seed() {
  try {
    await client.connect();
    const db = client.db();

    const productCol = db.collection('products');
    const menuCol = db.collection('menus');

    await productCol.deleteMany({});
    await productCol.insertMany(products);

    await menuCol.deleteMany({});
    await menuCol.insertMany(menus);

    console.log("✅ Products and Menus seeded.");
  } catch (err) {
    console.error("❌ Seeding error:", err);
  } finally {
    await client.close();
  }
}

seed();
