using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Data
{
    public class MainDbContext : DbContext
    {
        public MainDbContext (DbContextOptions<MainDbContext> options)
            : base(options)
        {
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Game>()
                .HasMany(it => it.Names)
                .WithOne()
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<TextSetting>()
                .HasMany(it => it.Hooks)
                .WithOne()
                .OnDelete(DeleteBehavior.Cascade);
        }

        public DbSet<Comment> Comment { get; set; }
        public DbSet<Game> Game { get; set; }
        public DbSet<GameItem> GameItem { get; set; }
        public DbSet<Reference> Reference { get; set; }
        public DbSet<Term> Term { get; set; }
        public DbSet<User> User { get; set; }
    }
}
