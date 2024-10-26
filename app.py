from task_tracker import create_app, db
from task_tracker.models import Task, User
from flask import render_template, request, redirect, url_for
from datetime import datetime

app = create_app()

@app.route('/')
def index():
    # Check for sorting query parameter
    sort = request.args.get('sort')

    if sort == 'assignment_date':
        tasks = Task.query.order_by(Task.assignment_date).all()
    elif sort == 'target_date':
        tasks = Task.query.order_by(Task.target_date).all()
    else:
        tasks = Task.query.all()
        
    return render_template('index.html', tasks=tasks)
@app.route('/completed_tasks')
def completed_tasks():
    completed_tasks = Task.query.filter_by(completed=True).all()
    return render_template('completed_tasks.html', tasks=completed_tasks)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        department = request.form['department']
        assigned_user_id = request.form.get('assigned_user')
        assignment_date = request.form.get('assignment_date')
        target_date = request.form.get('target_date')
        
        assignment_date_obj = datetime.strptime(assignment_date, '%Y-%m-%d').date() if assignment_date else None
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date() if target_date else None

        new_task = Task(
            title=title,
            description=description,
            department=department,
            assigned_user_id=int(assigned_user_id) if assigned_user_id else None,
            assignment_date=assignment_date_obj,
            target_date=target_date_obj
        )
        db.session.add(new_task)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('create.html', users=users)
@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        # Toggle the completion status and update the completed_date accordingly
        if task.completed:
            task.completed = False
            task.completed_date = None  # Clear the completion date when marking incomplete
        else:
            task.completed = True
            task.completed_date = datetime.now().date()  # Record completion date
        db.session.commit()
    return redirect(url_for('index'))
@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def view_task(task_id):
    task = Task.query.get(task_id)
    if request.method == 'POST':
        # Update description
        if 'description' in request.form:
            task.description = request.form['description']
        
        # Update due date
        if 'target_date' in request.form:
            new_target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()
            
            # Save current target date to history if changing
            if task.target_date and task.target_date != new_target_date:
                if task.due_date_history is None:
                    task.due_date_history = []
                task.due_date_history.append(task.target_date)
                task.edit_count += 1
            task.target_date = new_target_date
        
        db.session.commit()
        return redirect(url_for('view_task', task_id=task_id))
    
    return render_template('view_task.html', task=task)


if __name__ == '__main__':
    app.run(debug=True)
